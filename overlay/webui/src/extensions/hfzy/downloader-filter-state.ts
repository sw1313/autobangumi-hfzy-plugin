import { ref } from 'vue';
import type { QbTorrentInfo } from '#/downloader';
import type { HfzyMisc } from './types';

export type TorrentFilterMode = 'all' | 'done' | 'pending';

export const torrentFilterMode = ref<TorrentFilterMode>('all');

export function downloaderFilterEnabled() {
  const hfzy = useConfigStore().config.hfzy as Partial<HfzyMisc> | undefined;
  return hfzy?.downloader_filter !== false;
}

export function torrentIsComplete(torrent: QbTorrentInfo) {
  return Math.round(torrent.progress * 100) >= 100;
}

/** 下载器表格只保留这里返回 true 的行，表头全选才不会带上被筛掉的集。 */
export function torrentMatchesFilter(torrent: QbTorrentInfo) {
  if (!downloaderFilterEnabled() || torrentFilterMode.value === 'all') return true;
  const complete = torrentIsComplete(torrent);
  return torrentFilterMode.value === 'done' ? complete : !complete;
}
