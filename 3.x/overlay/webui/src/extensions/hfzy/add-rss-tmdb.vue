<script lang="ts" setup>
import { NSelect } from 'naive-ui';
import type { RSS } from '#/rss';
import { tmdbHint } from './tmdb-hint';

const props = defineProps<{ rss: RSS }>();

const { t } = useMyI18n();
const { config } = storeToRefs(useConfigStore());

const types = computed(() => [
  { label: t('topbar.add.tmdb_tv'), value: 'tv' },
  { label: t('topbar.add.tmdb_movie'), value: 'movie' },
]);

const visible = computed(
  () =>
    Boolean(config.value.hfzy?.tmdb_info) &&
    props.rss.parser === 'tmdb' &&
    !props.rss.aggregate
);

function clearHint() {
  tmdbHint.id = '';
  tmdbHint.mediaType = 'tv';
}

watch(visible, (show) => {
  if (!show) clearHint();
});

watch(
  () => props.rss.aggregate,
  (aggregate) => {
    if (aggregate) clearHint();
  }
);
</script>

<template>
  <div v-if="visible" class="options-row">
    <div class="option-item">
      <label class="option-label">{{ $t('topbar.add.tmdb_info') }}</label>
      <NSelect
        v-model:value="tmdbHint.mediaType"
        :options="types"
        class="type-select"
      />
    </div>
    <input
      v-model="tmdbHint.id"
      type="text"
      inputmode="numeric"
      class="form-input id-input"
      :placeholder="$t('topbar.add.tmdb_id')"
    />
  </div>
</template>

<style lang="scss" scoped>
.options-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: var(--color-surface-hover);
  border-radius: var(--radius-md);
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.option-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-secondary);
  white-space: nowrap;
}

.type-select {
  width: 140px;
}

.id-input {
  flex: 1;
  min-width: 140px;
}

.form-input {
  height: 40px;
  padding: 0 12px;
  font-size: 14px;
  font-family: inherit;
  color: var(--color-text);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: border-color var(--transition-fast),
    box-shadow var(--transition-fast);

  &:focus {
    border-color: var(--color-primary);
    box-shadow: 0 0 0 3px
      color-mix(in srgb, var(--color-primary) 15%, transparent);
  }

  &::placeholder {
    color: var(--color-text-muted);
  }
}

@media (max-width: 480px) {
  .options-row {
    flex-direction: column;
    align-items: stretch;
  }

  .option-item {
    justify-content: space-between;
    width: 100%;
  }

  .type-select,
  .id-input {
    width: 100%;
  }
}
</style>
