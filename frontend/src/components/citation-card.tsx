import { Card, CardContent } from "@/components/ui/card";
import { Citation } from "@/lib/api";

export function CitationCard({ citation }: { citation: Citation }) {
  return (
    <Card className="border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-950 mb-2">
      <CardContent className="p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-semibold text-blue-700 dark:text-blue-300 bg-blue-100 dark:bg-blue-900 px-2 py-0.5 rounded">
            {citation.source}
          </span>
          <span className="text-xs text-muted-foreground">
            Relevance: {(citation.score * 100).toFixed(0)}%
          </span>
        </div>
        <p className="text-sm text-muted-foreground line-clamp-3">{citation.text}</p>
      </CardContent>
    </Card>
  );
}