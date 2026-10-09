<script lang="ts" setup>
import type { SettingItem } from '#/components';
import type { HfzyMisc } from './types';

const { t } = useMyI18n();
const { getSettingGroup } = useConfigStore();
const hfzy = getSettingGroup('hfzy');

const items = computed<SettingItem<HfzyMisc>[]>(() => [
  {
    configKey: 'player_enable',
    label: () => t('config.hfzy_set.player_enable'),
    type: 'switch',
  },
  {
    configKey: 'downloader_filter',
    label: () => t('config.hfzy_set.downloader_filter'),
    description: t('config.hfzy_set.downloader_filter_desc'),
    type: 'switch',
  },
  {
    configKey: 'rss_name_priority',
    label: () => t('config.hfzy_set.rss_name_priority'),
    type: 'switch',
  },
  {
    configKey: 'rss_episode_count',
    label: () => t('config.hfzy_set.rss_episode_count'),
    description: t('config.hfzy_set.rss_episode_count_desc'),
    type: 'switch',
  },
  {
    configKey: 'rss_copy_fix',
    label: () => t('config.hfzy_set.rss_copy_fix'),
    description: t('config.hfzy_set.rss_copy_fix_desc'),
    type: 'switch',
  },
  {
    configKey: 'rss_filter_hit',
    label: () => t('config.hfzy_set.rss_filter_hit'),
    description: t('config.hfzy_set.rss_filter_hit_desc'),
    type: 'switch',
  },
  {
    configKey: 'tmdb_include_adult',
    label: () => t('config.hfzy_set.tmdb_include_adult'),
    description: t('config.hfzy_set.tmdb_include_adult_desc'),
    type: 'switch',
  },
  {
    configKey: 'tmdb_info',
    label: () => t('config.hfzy_set.tmdb_info'),
    description: t('config.hfzy_set.tmdb_info_desc'),
    type: 'switch',
  },
  {
    configKey: 'rss_form_season',
    label: () => t('config.hfzy_set.rss_form_season'),
    description: t('config.hfzy_set.rss_form_season_desc'),
    type: 'switch',
  },
  {
    configKey: 'special_rename',
    label: () => t('config.hfzy_set.special_rename'),
    description: t('config.hfzy_set.special_rename_desc'),
    type: 'switch',
  },
  {
    configKey: 'revision_group_fallback',
    label: () => t('config.hfzy_set.revision_group_fallback'),
    description: t('config.hfzy_set.revision_group_fallback_desc'),
    type: 'switch',
  },
  {
    configKey: 'revision_single_video',
    label: () => t('config.hfzy_set.revision_single_video'),
    description: t('config.hfzy_set.revision_single_video_desc'),
    type: 'switch',
  },
  {
    configKey: 'revision_conflict_policy',
    label: () => t('config.hfzy_set.revision_conflict_policy'),
    description: t('config.hfzy_set.revision_conflict_policy_desc'),
    type: 'select',
    prop: {
      items: [
        {
          id: 0,
          value: 'hold',
          label: t('config.hfzy_set.revision_hold'),
        },
        {
          id: 1,
          value: 'replace',
          label: t('config.hfzy_set.revision_replace'),
        },
      ],
    },
  },
]);
</script>

<template>
  <ab-fold-panel :title="$t('config.hfzy_set.title')">
    <p class="hfzy-desc">{{ $t('config.hfzy_set.desc') }}</p>
    <div space-y-8>
      <ab-setting
        v-for="item in items"
        :key="item.configKey"
        v-bind="item"
        v-model:data="hfzy[item.configKey]"
      />
    </div>
  </ab-fold-panel>
</template>

<style scoped>
.hfzy-desc {
  margin-bottom: 12px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.5;
}
</style>
