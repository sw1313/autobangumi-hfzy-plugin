import type { Component } from 'vue';
import type { BangumiRule } from '#/bangumi';
import type { Config } from '#/config';
import type { QbTorrentInfo } from '#/downloader';
import ConfigHfzy from './config-hfzy.vue';
import DownloaderFilter from './downloader-filter.vue';
import { torrentMatchesFilter } from './downloader-filter-state';
import DownloaderPlayButton from './downloader-play-button.vue';
import RssEpisodeCount from './rss-episode-count.vue';
import en from './i18n/en.json';
import zhCN from './i18n/zh-CN.json';

export interface LocalExtensionsRegistry {
  configSections: Array<{
    id: string;
    titleKey: string;
    component: Component;
    groups: Array<keyof Config>;
    keywords: string[];
  }>;
  downloaderNameActions: Component<{ torrent: QbTorrentInfo }>[];
  downloaderToolbars: Component[];
  downloaderTorrentVisible: Array<(torrent: QbTorrentInfo) => boolean>;
  bangumiMetaExtras: Component<{ rule: BangumiRule }>[];
  i18n: Record<string, Record<string, unknown>>;
}

function deepMerge(
  target: Record<string, unknown>,
  source: Record<string, unknown>
): Record<string, unknown> {
  for (const [key, value] of Object.entries(source)) {
    if (
      value &&
      typeof value === 'object' &&
      !Array.isArray(value) &&
      target[key] &&
      typeof target[key] === 'object' &&
      !Array.isArray(target[key])
    ) {
      deepMerge(
        target[key] as Record<string, unknown>,
        value as Record<string, unknown>
      );
    } else {
      target[key] = value;
    }
  }
  return target;
}

export function registerHfzyExtension(ext: LocalExtensionsRegistry) {
  ext.configSections.push({
    id: 'hfzy',
    titleKey: 'config.hfzy_set.title',
    component: ConfigHfzy,
    groups: ['hfzy'],
    keywords: [
      'hfzy',
      'player',
      'rss',
      'play',
      '筛选',
      '完成',
      'copy',
      'filter',
      'episode',
      '集数',
      '复制',
      '过滤',
      '成人',
      'tmdb',
      '季度',
      '修订',
      '冲突',
      'v2',
      '字幕',
      '压缩包',
      '皇甫朝云',
    ],
  });
  ext.downloaderNameActions.push(DownloaderPlayButton);
  ext.downloaderToolbars.push(DownloaderFilter);
  ext.downloaderTorrentVisible.push(torrentMatchesFilter);
  ext.bangumiMetaExtras.push(RssEpisodeCount);
  ext.i18n['zh-CN'] = deepMerge(ext.i18n['zh-CN'] ?? {}, zhCN);
  ext.i18n.en = deepMerge(ext.i18n.en ?? {}, en);
}
