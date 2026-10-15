import { Jieba } from '@node-rs/jieba';
import { CommonConst } from '~/server/domain/constants';

// Python jieba is initialized in the lifespan hook. @node-rs/jieba's Jieba loads its default
// dictionary on construction, so we lazily build one shared instance.
let instance: Jieba | null = null;

export function jieba(): Jieba {
  if (!instance) instance = new Jieba();
  return instance;
}

export function initJieba(): void {
  jieba();
}

// Mirrors: TOKEN_SEPARATOR.join([t.strip() for t in jieba.cut_for_search(text) if t.strip()])
export function tokenize(text: string | null | undefined): string {
  if (!text) return '';
  return jieba()
    .cutForSearch(text)
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
    .join(CommonConst.TOKEN_SEPARATOR);
}

// Mirrors: TOKEN_SEPARATOR.join(jieba.cut_for_search(text)) (no per-token strip filter).
export function tokenizeRaw(text: string): string {
  return jieba().cutForSearch(text).join(CommonConst.TOKEN_SEPARATOR);
}

// Mirrors: [seg for part in text.split() for seg in jieba.cut(part) if seg.strip()]
export function cutWords(text: string): string[] {
  const words: string[] = [];
  for (const part of text.split(/\s+/).filter(Boolean)) {
    for (const seg of jieba().cut(part)) {
      if (seg.trim().length > 0) words.push(seg);
    }
  }
  return words;
}

// Mirrors: ' '.join(jieba.cut(text))
export function cutJoin(text: string): string {
  return jieba().cut(text).join(' ');
}
