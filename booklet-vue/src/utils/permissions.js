/**
 * Check whether the current user has a specific permission.
 *
 * @param {string}  perm        - Permission code (e.g. 'sales.create_invoice').
 * @param {string[]} permissions - Array of permission codes assigned to the user.
 * @param {boolean} isSuperuser - Whether the user is a superuser.
 * @returns {boolean}
 */
export function hasPermission(perm, permissions, isSuperuser) {
  if (isSuperuser) return true
  if (!permissions || !Array.isArray(permissions)) return false
  return permissions.includes(perm)
}

/**
 * Check whether a plan includes a specific feature.
 *
 * @param {string}  feature    - Feature identifier (e.g. 'multi_branch').
 * @param {object|null} planLimits - The plan limits object from the API.
 * @returns {boolean}
 */
export function hasPlanFeature(feature, planLimits) {
  if (!planLimits) return false
  if (planLimits.plan === 'enterprise') return true
  if (Array.isArray(planLimits.features)) {
    return planLimits.features.includes(feature)
  }
  return false
}

/**
 * Check whether the business can create another branch.
 *
 * @param {object} planLimits  - The plan limits object.
 * @param {number} branchCount - Current number of branches.
 * @returns {boolean}
 */
export function canCreateBranch(planLimits, branchCount) {
  if (!planLimits) return false
  const max = planLimits.max_branches ?? Infinity
  return branchCount < max
}

/**
 * Check whether the business can create another user.
 *
 * @param {object} planLimits - The plan limits object.
 * @param {number} userCount  - Current number of users.
 * @returns {boolean}
 */
export function canCreateUser(planLimits, userCount) {
  if (!planLimits) return false
  const max = planLimits.max_users ?? Infinity
  return userCount < max
}
