import { useConfigStore } from '@/store/config';

/** Copy that still works when the page is opened over plain http. */

function copyWithSelection(text: string): boolean {
  const area = document.createElement('textarea');
  area.value = text;
  area.setAttribute('readonly', '');
  area.style.position = 'fixed';
  area.style.top = '0';
  area.style.left = '0';
  area.style.opacity = '0';
  area.style.pointerEvents = 'none';
  const active = document.activeElement;
  const parent =
    active instanceof Element
      ? active.closest('[role="dialog"]') ?? document.body
      : document.body;
  parent.appendChild(area);
  area.focus();
  area.select();
  area.setSelectionRange(0, area.value.length);
  let ok = false;
  try {
    ok = document.execCommand('copy');
  } catch {
    ok = false;
  } finally {
    parent.removeChild(area);
  }
  return ok;
}

function copyFixEnabled(): boolean {
  try {
    return useConfigStore().config.hfzy?.rss_copy_fix !== false;
  } catch {
    return true;
  }
}

export async function copyRssLinkText(text: string): Promise<boolean> {
  const clipboard = navigator.clipboard?.writeText;
  const secure = window.isSecureContext !== false;
  if (!copyFixEnabled()) {
    if (!clipboard) return false;
    await clipboard.call(navigator.clipboard, text);
    return true;
  }
  if (secure && clipboard) {
    try {
      await clipboard.call(navigator.clipboard, text);
      return true;
    } catch {
      return copyWithSelection(text);
    }
  }
  return copyWithSelection(text);
}
