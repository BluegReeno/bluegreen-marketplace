#!/usr/bin/env python3
"""Export a .docx to PDF with LibreOffice, filling the table of contents first.

A plain `soffice --convert-to pdf` leaves the TOC empty: Word computes it when the file opens,
LibreOffice does not. This drives LibreOffice through its UNO bridge: load, update every index
(twice, since filling the TOC shifts page numbers), then export with form fields.

Usage (python3 must be able to `import uno`, i.e. LibreOffice's Python bridge):
    python3 scripts/pdf_export.py doc.docx [-o doc.pdf]
Exit code 3 when the bridge is missing, so callers can fall back to `soffice --convert-to`.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time

try:
    import uno
    from com.sun.star.beans import PropertyValue
except ImportError:
    sys.exit(3)


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    src = os.path.abspath(args.source)
    out = os.path.abspath(args.output or os.path.splitext(src)[0] + ".pdf")

    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("soffice not found")
    profile = tempfile.mkdtemp(prefix="lo-profile-")
    port = 2000 + os.getpid() % 5000
    proc = subprocess.Popen(
        [soffice, "--headless", "--invisible", "--norestore", "--nologo",
         f"-env:UserInstallation=file://{profile}",
         f"--accept=socket,host=127.0.0.1,port={port};urp;"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        resolver = uno.getComponentContext().ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", uno.getComponentContext())
        ctx = None
        for _ in range(60):
            try:
                ctx = resolver.resolve(f"uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(0.5)
        if ctx is None:
            sys.exit("LibreOffice did not start")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(src), "_blank", 0, (prop("Hidden", True),))
        indexes = doc.getDocumentIndexes()
        for _ in range(2):
            for i in range(indexes.getCount()):
                indexes.getByIndex(i).update()
        filter_data = uno.Any("[]com.sun.star.beans.PropertyValue", (prop("ExportFormFields", True),))
        doc.storeToURL(uno.systemPathToFileUrl(out),
                       (prop("FilterName", "writer_pdf_Export"), prop("FilterData", filter_data)))
        doc.close(True)
        print(out)
    finally:
        try:
            desktop.terminate()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
