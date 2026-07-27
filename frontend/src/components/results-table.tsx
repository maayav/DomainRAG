"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ExperimentResult {
  config: string;
  chunk_size: number;
  chunk_overlap: number;
  top_k: number;
  faithfulness?: number;
  answer_relevancy?: number;
  context_recall?: number;
  context_precision?: number;
  latency_avg?: number;
}

export function ResultsTable({ results }: { results: ExperimentResult[] }) {
  if (!results || results.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Experiment Results</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No results yet. Run experiments from the backend.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Experiment Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Config</TableHead>
              <TableHead>Chunk Size</TableHead>
              <TableHead>Overlap</TableHead>
              <TableHead>Top-K</TableHead>
              <TableHead>Faithfulness</TableHead>
              <TableHead>Relevancy</TableHead>
              <TableHead>Recall</TableHead>
              <TableHead>Precision</TableHead>
              <TableHead>Latency (s)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {results.map((r, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{r.config}</TableCell>
                <TableCell>{r.chunk_size}</TableCell>
                <TableCell>{r.chunk_overlap}</TableCell>
                <TableCell>{r.top_k}</TableCell>
                <TableCell>{r.faithfulness?.toFixed(3) ?? "-"}</TableCell>
                <TableCell>{r.answer_relevancy?.toFixed(3) ?? "-"}</TableCell>
                <TableCell>{r.context_recall?.toFixed(3) ?? "-"}</TableCell>
                <TableCell>{r.context_precision?.toFixed(3) ?? "-"}</TableCell>
                <TableCell>{r.latency_avg?.toFixed(2) ?? "-"}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
