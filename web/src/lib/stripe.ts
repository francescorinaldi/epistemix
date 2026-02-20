/**
 * Stripe billing helpers.
 * Usage-based billing: per-audit pricing.
 *
 * Plans:
 *   free: 3 audits/month, 2 cycles max
 *   pro ($29/mo): unlimited audits, full cycles, export
 *   enterprise: API access, custom axioms, BYOK, team features
 */

export const PLAN_LIMITS = {
  free: { audits_per_month: 3, max_cycles: 2 },
  pro: { audits_per_month: Infinity, max_cycles: 10 },
  enterprise: { audits_per_month: Infinity, max_cycles: 10 },
} as const;

export type PlanName = keyof typeof PLAN_LIMITS;

export function canStartAudit(
  plan: PlanName,
  auditsThisMonth: number
): boolean {
  return auditsThisMonth < PLAN_LIMITS[plan].audits_per_month;
}

export function maxCyclesForPlan(plan: PlanName): number {
  return PLAN_LIMITS[plan].max_cycles;
}
