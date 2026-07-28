import type { MissionSummary } from "../hal-types";

function formatDate(iso: string): string {
  return iso.slice(0, 10);
}

export function MissionList({
  missions,
  onSelect,
}: {
  missions: MissionSummary[];
  onSelect: (missionId: string) => void;
}) {
  if (missions.length === 0) {
    return <p className="text-sm text-muted-foreground">Aucune mission trouvée.</p>;
  }

  return (
    <table className="w-full border-collapse text-sm">
      <thead>
        <tr className="border-b text-left text-muted-foreground">
          <th className="py-2 pr-4">Date</th>
          <th className="py-2 pr-4">Nom</th>
          <th className="py-2 pr-4">Type</th>
          <th className="py-2 pr-4">Statut</th>
          <th className="py-2 pr-4">Bâtiment / Adresse</th>
        </tr>
      </thead>
      <tbody>
        {missions.map((m) => (
          <tr
            key={m.id}
            className="cursor-pointer border-b hover:bg-accent"
            onClick={() => onSelect(m.id)}
          >
            <td className="py-2 pr-4">{formatDate(m.created_at)}</td>
            <td className="py-2 pr-4">{m.name}</td>
            <td className="py-2 pr-4">{m.type}</td>
            <td className="py-2 pr-4">{m.status}</td>
            <td className="py-2 pr-4">{m.building ? `${m.building.name} — ${m.building.address}` : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
