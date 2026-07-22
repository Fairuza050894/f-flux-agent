function createAliases(...aliases) {
  return Object.freeze(aliases)
}

export const RESULT_METRIC_ALIASES =
  Object.freeze({
    passed: createAliases(
      'passed',
      'passed_count',
      'passedCount',
    ),

    failed: createAliases(
      'failed',
      'failed_count',
      'failedCount',
    ),

    needReview: createAliases(
      'need_review',
      'needReview',
      'need_review_count',
      'needReviewCount',
    ),

    skipped: createAliases(
      'skipped',
      'skipped_count',
      'skippedCount',
    ),

    blocked: createAliases(
      'blocked',
      'blocked_count',
      'blockedCount',
    ),

    bugsFound: createAliases(
      'bugs_found',
      'bugsFound',
      'bug_count',
      'bugCount',
    ),

    warnings: createAliases(
      'non_blocking_warnings',
      'nonBlockingWarnings',
      'warnings',
      'warning_count',
      'warningCount',
    ),
  })

export const RESULT_TERMINAL_STATUSES =
  Object.freeze([
    'passed',
    'failed',
    'need_review',
    'completed',
  ])

export const RESULT_UNSUPPORTED_STATUSES =
  Object.freeze([
    'not_implemented',
    'unsupported',
  ])

export const RESULT_ACTIVE_STATUSES =
  Object.freeze([
    'queued',
    'pending',
    'created',
    'running',
    'in_progress',
    'processing',
  ])

export const EMPTY_RESULT_METRICS =
  Object.freeze({
    passed: 0,
    failed: 0,
    needReview: 0,
    skipped: 0,
    blocked: 0,
    bugsFound: 0,
    warnings: 0,
  })
