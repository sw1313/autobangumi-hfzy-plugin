<script lang="ts" setup>
import { Down } from '@icon-park/vue-next';
import {
  downloaderFilterEnabled,
  torrentFilterMode,
  type TorrentFilterMode,
} from './downloader-filter-state';

const { groups } = storeToRefs(useDownloaderStore());
const { t } = useMyI18n();
const pageActive = ref(false);

const enabled = computed(() => pageActive.value && downloaderFilterEnabled());

function setMode(next: TorrentFilterMode) {
  if (torrentFilterMode.value === next) return;
  torrentFilterMode.value = next;
}

const menuItems = computed(() =>
  (
    [
      ['all', t('downloader.filter.all')],
      ['done', t('downloader.filter.done')],
      ['pending', t('downloader.filter.pending')],
    ] as const
  ).map(([key, label]) => ({
    key,
    label: torrentFilterMode.value === key ? `✓ ${label}` : label,
    handler: () => setMode(key),
  }))
);

const currentLabel = computed(() => {
  if (torrentFilterMode.value === 'done') return t('downloader.filter.done');
  if (torrentFilterMode.value === 'pending') return t('downloader.filter.pending');
  return t('downloader.filter.all');
});

const nothingVisible = computed(() => {
  if (!enabled.value || torrentFilterMode.value === 'all') return false;
  return (
    groups.value.length > 0 &&
    groups.value.every((group) =>
      group.torrents.every((torrent) => {
        const complete = Math.round(torrent.progress * 100) >= 100;
        return torrentFilterMode.value === 'done' ? !complete : complete;
      })
    )
  );
});

onMounted(() => {
  pageActive.value = true;
});
onActivated(() => {
  pageActive.value = true;
});
onDeactivated(() => {
  pageActive.value = false;
});
</script>

<template>
  <Teleport v-if="enabled" to=".page-title">
    <div class="hfzy-downloader-filter">
      <ab-menu :items="menuItems" align="right">
        <template #trigger>
          <ab-button variant="ghost" size="sm">
            {{ currentLabel }}
            <Down :size="14" />
          </ab-button>
        </template>
      </ab-menu>
    </div>
  </Teleport>
  <div v-if="nothingVisible" class="hfzy-filter-empty">
    {{
      torrentFilterMode === 'done'
        ? $t('downloader.filter.empty_done')
        : $t('downloader.filter.empty_pending')
    }}
  </div>
</template>

<style lang="scss" scoped>
.hfzy-downloader-filter {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
}

.hfzy-filter-empty {
  color: var(--color-text-secondary);
  font-size: 14px;
  text-align: center;
  padding: 24px 0;
}
</style>
