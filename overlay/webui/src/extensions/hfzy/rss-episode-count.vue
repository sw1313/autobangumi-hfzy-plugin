<script lang="ts" setup>
import type { BangumiRule } from '#/bangumi';
import { hfzyApi } from './api';
import { setFilterHits } from './filter-hits';

const props = defineProps<{
  rule: BangumiRule;
}>();

const { t, lang } = useMyI18n();
const { config } = storeToRefs(useConfigStore());

const countEnabled = computed(
  () => config.value.hfzy?.rss_episode_count !== false
);
const hitEnabled = computed(() => config.value.hfzy?.rss_filter_hit !== false);
const versions = ref(0);
const videos = ref<number | null>(null);
const invalid = ref(false);
const failed = ref(false);

let ticket = 0;
let timer: ReturnType<typeof setTimeout> | undefined;

const link = computed(() => props.rule.rss_link?.[0]?.trim() ?? '');
const visible = computed(() => countEnabled.value && link.value !== '');
const tracking = computed(
  () => (countEnabled.value || hitEnabled.value) && link.value !== ''
);

const pending = computed(
  () => videos.value === null && !invalid.value && !failed.value
);

const label = computed(() => {
  if (invalid.value) return t('config.hfzy_set.episode_invalid');
  if (failed.value) return t('config.hfzy_set.episode_failed');
  if (videos.value === null) return '…';
  return lang.value === 'en'
    ? `${versions.value} versions, ${videos.value} videos`
    : `共 ${versions.value} 版 ${videos.value} 个视频`;
});

const hint = computed(() => {
  if (videos.value === null) return '';
  return lang.value === 'en'
    ? 'Versions are the release variants left after filters'
    : '版是过滤后剩下的发布版本，视频是剩下的条目';
});

function schedule() {
  if (timer) clearTimeout(timer);
  timer = setTimeout(() => {
    timer = undefined;
    void refresh();
  }, 400);
}

async function refresh() {
  const current = ++ticket;
  if (!tracking.value) {
    versions.value = 0;
    videos.value = null;
    invalid.value = false;
    failed.value = false;
    setFilterHits([]);
    return;
  }
  versions.value = 0;
  videos.value = null;
  invalid.value = false;
  failed.value = false;
  setFilterHits([]);
  const season = Number.isFinite(props.rule.season) ? props.rule.season : 1;
  try {
    const data = await hfzyApi.rssEpisodeCount({
      rss_link: link.value,
      filter: props.rule.filter ?? [],
      season,
      episode_type: props.rule.episode_type || 'episode',
    });
    if (current !== ticket) return;
    versions.value = data.versions;
    videos.value = data.videos;
    invalid.value = false;
    failed.value = false;
    setFilterHits(hitEnabled.value ? data.hits ?? [] : []);
  } catch (error: unknown) {
    if (current !== ticket) return;
    const status = (error as { status?: number }).status;
    versions.value = 0;
    videos.value = null;
    setFilterHits([]);
    invalid.value = status === 400;
    failed.value = !invalid.value;
  }
}

watch(
  () => [
    countEnabled.value,
    hitEnabled.value,
    link.value,
    (props.rule.filter ?? []).join('\n'),
    props.rule.season,
    props.rule.episode_type,
  ],
  schedule,
  { immediate: true }
);

onBeforeUnmount(() => {
  ticket += 1;
  if (timer) clearTimeout(timer);
  setFilterHits([]);
});
</script>

<template>
  <span v-if="visible" class="rss-episode-count" :title="hint">
    <span class="rss-episode-count__sep">·</span>
    <span
      class="rss-episode-count__value"
      :class="{
        'is-empty': videos === 0,
        'is-invalid': invalid || failed,
        'is-loading': pending,
      }"
    >
      {{ label }}
    </span>
  </span>
</template>

<style lang="scss" scoped>
.rss-episode-count {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.rss-episode-count__sep {
  color: var(--color-text-muted);
}

.rss-episode-count__value {
  font-size: 13px;
  color: var(--color-text-secondary);
  white-space: nowrap;

  &.is-empty,
  &.is-invalid {
    color: var(--color-warning);
  }

  &.is-loading {
    color: var(--color-text-muted);
  }
}
</style>
