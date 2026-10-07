export interface HfzyMisc {
  player_enable: boolean;
  rss_name_priority: boolean;
  rss_episode_count: boolean;
  rss_copy_fix: boolean;
  rss_filter_hit: boolean;
  tmdb_include_adult: boolean;
  rss_form_season: boolean;
}

export const defaultHfzyConfig: HfzyMisc = {
  player_enable: true,
  rss_name_priority: true,
  rss_episode_count: true,
  rss_copy_fix: true,
  rss_filter_hit: true,
  tmdb_include_adult: true,
  rss_form_season: true,
};
