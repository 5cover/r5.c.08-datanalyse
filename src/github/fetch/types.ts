// src/types.ts
export interface RepositoryKey {
  owner: string;
  name: string;
}

export interface Repository extends RepositoryKey {
  id: number;
  description: string;
  language: string;
  n_stars: number;
  n_forks: number;
  n_watchers: number;
  n_commits: number;
  size: number;
  created_at: string;
  tags: string[];
}

export interface LanguageStats {
  name: string;
  lines: number;
  code: number;
  comments: number;
  blanks: number;
  complexity: number;
  bytes: number;
  files: number;
}

export interface RepositoryResult {
  repository: string;
  metadata: Repository;
  languages: LanguageStats[];
  total_lines: number;
  total_files: number;
  analysis_method: 'countloc_api' | 'scc_local';
  error?: string;
}