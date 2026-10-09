<script lang="ts" setup>
import { PlayOne } from '@icon-park/vue-next';
import type { QbTorrentInfo } from '#/downloader';
import { playerApi } from './player-api';

const props = defineProps<{
  torrent: QbTorrentInfo;
}>();

const { config } = storeToRefs(useConfigStore());
const message = useMessage();
const { t } = useMyI18n();
const loading = ref(false);
const enabled = computed(() => config.value.hfzy?.player_enable !== false);

function absoluteUrl(url: string): string {
  if (/^https?:\/\//i.test(url)) return url;
  return new URL(url, window.location.origin).toString();
}

async function openWeb() {
  loading.value = true;
  try {
    const result = await playerApi.resolveTorrent(props.torrent.hash);
    const file = result.files[0];
    if (!file) {
      message.warning(t('downloader.player.no_media'));
      return;
    }
    window.open(absoluteUrl(file.url), '_blank', 'noopener,noreferrer');
  } catch {
    message.error(t('downloader.player.resolve_failed'));
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <button
    v-if="enabled"
    class="downloader-play-btn"
    :disabled="loading"
    :title="$t('downloader.player.web')"
    @click.stop="openWeb"
  >
    <PlayOne theme="outline" size="14" />
  </button>
</template>

<style lang="scss" scoped>
.downloader-play-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  margin: 0;
  padding: 0;
  flex-shrink: 0;
  position: relative;
  transform: translateY(2px);
  color: var(--color-primary);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background-color var(--transition-fast),
    border-color var(--transition-fast);

  &:hover:not(:disabled) {
    background: var(--color-surface-hover);
    border-color: var(--color-primary);
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
}
</style>
