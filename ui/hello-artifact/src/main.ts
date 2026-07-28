import "./index.css";

const root = document.getElementById("app")!;
let count = 0;

function render() {
  root.innerHTML = `
    <h1 class="text-2xl font-bold">Hello Artifact</h1>
    <button class="px-3 py-1 bg-blue-600 text-white rounded" id="btn">Count: ${count}</button>
  `;
  document.getElementById("btn")!.addEventListener("click", () => {
    count++;
    render();
  });
}
render();
