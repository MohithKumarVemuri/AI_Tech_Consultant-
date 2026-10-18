export interface EditDiffResult {
  similarity: number; // 0.0 to 1.0
  isUnchanged: boolean;
  normalizedOriginal: string;
  normalizedFinal: string;
  wordCountDiff: number;
}

export function normalizeText(text: string): string {
  return text
    .toLowerCase()
    .replace(/\r\n/g, "\n")
    .replace(/[^\w\s]/g, "")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Calculates normalized text comparison + similarity score.
 * Spec rule: "unchanged" = similarity >= 0.98 and no semantic edit flag.
 */
export function calculateEditDiff(draftReply: string, finalReply: string): EditDiffResult {
  const normOriginal = normalizeText(draftReply);
  const normFinal = normalizeText(finalReply);

  if (normOriginal === normFinal) {
    return {
      similarity: 1.0,
      isUnchanged: true,
      normalizedOriginal: normOriginal,
      normalizedFinal: normFinal,
      wordCountDiff: 0,
    };
  }

  // Token Jaccard / Levenshtein hybrid
  const origTokens = normOriginal.split(" ").filter(Boolean);
  const finalTokens = normFinal.split(" ").filter(Boolean);

  const origSet = new Set(origTokens);
  const finalSet = new Set(finalTokens);

  const intersection = new Set([...origSet].filter((x) => finalSet.has(x)));
  const union = new Set([...origSet, ...finalSet]);

  const jaccard = union.size === 0 ? 1.0 : intersection.size / union.size;

  // Simple string distance ratio
  const maxLen = Math.max(normOriginal.length, normFinal.length);
  const diffLen = Math.abs(normOriginal.length - normFinal.length);
  const lengthRatio = maxLen === 0 ? 1.0 : 1.0 - diffLen / maxLen;

  const similarity = Math.round((jaccard * 0.7 + lengthRatio * 0.3) * 1000) / 1000;
  const isUnchanged = similarity >= 0.98;

  return {
    similarity,
    isUnchanged,
    normalizedOriginal: normOriginal,
    normalizedFinal: normFinal,
    wordCountDiff: finalTokens.length - origTokens.length,
  };
}
