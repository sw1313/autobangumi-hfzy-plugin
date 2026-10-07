import { ref } from 'vue';

/** Filter terms that matched at least one title in the current RSS. */
export const filterHits = ref<string[]>([]);

export function setFilterHits(hits: string[]) {
  filterHits.value = hits;
}
