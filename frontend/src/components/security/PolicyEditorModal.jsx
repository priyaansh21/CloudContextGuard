import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react'
import Modal from '../common/Modal'
import { useApi } from '../../hooks/useApi'
import { getRoles, getVpcs, updatePolicy } from '../../services/api'

const SENSITIVE_FIELDS = ['trusted_vpc', 'mfa_required', 'external_access_allowed', 'max_risk_score']

const FIELD_LABELS = {
  name: 'Name',
  description: 'Description',
  required_role: 'Required role',
  trusted_vpc: 'Trusted VPC',
  mfa_required: 'MFA required',
  max_risk_score: 'Max risk score',
  external_access_allowed: 'External access allowed',
  is_enabled: 'Enabled',
}

function toFormState(policy) {
  return {
    name: policy.name,
    description: policy.description || '',
    required_role: policy.required_role || '',
    trusted_vpc: policy.trusted_vpc || '',
    mfa_required: policy.mfa_required,
    max_risk_score: policy.max_risk_score ?? '',
    external_access_allowed: policy.external_access_allowed,
    is_enabled: policy.is_enabled,
  }
}

function toPayload(form) {
  return {
    name: form.name,
    description: form.description.trim() === '' ? null : form.description,
    required_role: form.required_role === '' ? null : form.required_role,
    trusted_vpc: form.trusted_vpc === '' ? null : form.trusted_vpc,
    mfa_required: form.mfa_required,
    max_risk_score: form.max_risk_score === '' ? null : Number(form.max_risk_score),
    external_access_allowed: form.external_access_allowed,
    is_enabled: form.is_enabled,
  }
}

function displayValue(field, value) {
  if (value === '' || value === null || value === undefined) return 'none'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value)
}

function diffPayload(original, payload) {
  const changes = []
  for (const field of Object.keys(FIELD_LABELS)) {
    if (original[field] !== payload[field]) {
      changes.push({ field, label: FIELD_LABELS[field], before: original[field], after: payload[field] })
    }
  }
  return changes
}

export default function PolicyEditorModal({ policy, onClose, onSaved }) {
  const [form, setForm] = useState(() => toFormState(policy))
  const [step, setStep] = useState('editing') // editing | confirming | saving | success | error
  const [errorMessage, setErrorMessage] = useState('')
  const [savedChanges, setSavedChanges] = useState([])

  const roles = useApi(getRoles)
  const vpcs = useApi(getVpcs)

  useEffect(() => {
    setForm(toFormState(policy))
    setStep('editing')
    setErrorMessage('')
  }, [policy])

  const originalPayload = useMemo(
    () => ({
      name: policy.name,
      description: policy.description ?? null,
      required_role: policy.required_role ?? null,
      trusted_vpc: policy.trusted_vpc ?? null,
      mfa_required: policy.mfa_required,
      max_risk_score: policy.max_risk_score ?? null,
      external_access_allowed: policy.external_access_allowed,
      is_enabled: policy.is_enabled,
    }),
    [policy]
  )

  const payload = toPayload(form)
  const changes = diffPayload(originalPayload, payload)
  const hasSensitiveChange = changes.some((change) => SENSITIVE_FIELDS.includes(change.field))

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  function handleSaveClick() {
    if (changes.length === 0) return
    setStep(hasSensitiveChange ? 'confirming' : 'saving')
    if (!hasSensitiveChange) save()
  }

  async function save() {
    setStep('saving')
    try {
      await updatePolicy(policy.id, payload)
      setSavedChanges(changes)
      setStep('success')
      onSaved()
    } catch (err) {
      setErrorMessage(err.message)
      setStep('error')
    }
  }

  const isSuccess = step === 'success'

  return (
    <Modal open onClose={onClose} title={`Edit Policy — ${policy.name}`} wide>
      {isSuccess ? (
        <div className="flex flex-col items-center gap-3 py-8 text-center">
          <CheckCircle2 className="h-9 w-9 text-status-safe" aria-hidden="true" />
          <p className="text-base font-semibold text-text-primary">Policy updated successfully.</p>
          {savedChanges.length > 0 && (
            <ul className="w-full max-w-md space-y-1.5 text-left">
              {savedChanges.map((change) => (
                <li key={change.field} className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs">
                  <span className="font-medium text-text-primary">{change.label}: </span>
                  <span className="text-text-muted line-through">{displayValue(change.field, change.before)}</span>
                  <span className="mx-1 text-text-muted">→</span>
                  <span className="font-semibold text-status-safe">{displayValue(change.field, change.after)}</span>
                </li>
              ))}
            </ul>
          )}
          <button
            type="button"
            onClick={onClose}
            className="mt-2 rounded-md border border-border bg-surface-2 px-4 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-3"
          >
            Close
          </button>
        </div>
      ) : step === 'confirming' ? (
        <div className="space-y-4">
          <div className="flex items-start gap-2 rounded-lg border border-status-warning/40 bg-status-warning-bg p-4">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-status-warning" aria-hidden="true" />
            <p className="text-sm text-text-primary">
              Changing this policy will alter authorization decisions for protected resources.
            </p>
          </div>
          <div>
            <p className="mb-1.5 text-[11px] uppercase tracking-wide text-text-muted">Pending changes</p>
            <ul className="space-y-1.5">
              {changes.map((change) => (
                <li key={change.field} className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs">
                  <span className="font-medium text-text-primary">{change.label}: </span>
                  <span className="text-text-muted line-through">{displayValue(change.field, change.before)}</span>
                  <span className="mx-1 text-text-muted">→</span>
                  <span className="font-semibold text-status-warning">{displayValue(change.field, change.after)}</span>
                </li>
              ))}
            </ul>
          </div>
          {errorMessage && <p className="text-sm text-status-critical">{errorMessage}</p>}
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setStep('editing')}
              className="rounded-md border border-border bg-surface-2 px-4 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-3"
            >
              Back
            </button>
            <button
              type="button"
              onClick={save}
              className="flex items-center gap-2 rounded-md border border-status-critical/40 bg-status-critical-bg px-4 py-1.5 text-sm font-semibold text-status-critical hover:bg-status-critical/20"
            >
              CONFIRM POLICY CHANGE
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="block text-xs font-medium text-text-muted sm:col-span-2">
              Policy Name
              <input
                type="text"
                value={form.name}
                onChange={(e) => update('name', e.target.value)}
                className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary focus:border-status-info focus:outline-none"
              />
            </label>

            <label className="block text-xs font-medium text-text-muted sm:col-span-2">
              Description
              <textarea
                value={form.description}
                onChange={(e) => update('description', e.target.value)}
                rows={2}
                className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary focus:border-status-info focus:outline-none"
              />
            </label>

            <label className="block text-xs font-medium text-text-muted">
              Required Role
              <select
                value={form.required_role}
                onChange={(e) => update('required_role', e.target.value)}
                disabled={roles.loading}
                className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary focus:border-status-info focus:outline-none"
              >
                <option value="">— None —</option>
                {(roles.data || []).map((role) => (
                  <option key={role.id} value={role.name}>
                    {role.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-xs font-medium text-text-muted">
              Trusted VPC
              <select
                value={form.trusted_vpc}
                onChange={(e) => update('trusted_vpc', e.target.value)}
                disabled={vpcs.loading}
                className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary focus:border-status-info focus:outline-none"
              >
                <option value="">— None —</option>
                {(vpcs.data || []).map((vpc) => (
                  <option key={vpc.id} value={vpc.name}>
                    {vpc.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block text-xs font-medium text-text-muted">
              Maximum Risk Score
              <input
                type="number"
                min={0}
                max={100}
                value={form.max_risk_score}
                onChange={(e) => update('max_risk_score', e.target.value)}
                placeholder="No limit"
                className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-1.5 text-sm text-text-primary focus:border-status-info focus:outline-none"
              />
            </label>

            <div className="flex flex-col gap-2 pt-1">
              <label className="flex items-center gap-2 text-sm text-text-primary">
                <input
                  type="checkbox"
                  checked={form.mfa_required}
                  onChange={(e) => update('mfa_required', e.target.checked)}
                  className="h-4 w-4 accent-status-accent"
                />
                MFA Required
              </label>
              <label className="flex items-center gap-2 text-sm text-text-primary">
                <input
                  type="checkbox"
                  checked={form.external_access_allowed}
                  onChange={(e) => update('external_access_allowed', e.target.checked)}
                  className="h-4 w-4 accent-status-accent"
                />
                External Access Allowed
              </label>
              <label className="flex items-center gap-2 text-sm text-text-primary">
                <input
                  type="checkbox"
                  checked={form.is_enabled}
                  onChange={(e) => update('is_enabled', e.target.checked)}
                  className="h-4 w-4 accent-status-accent"
                />
                Enabled
              </label>
            </div>
          </div>

          {step === 'error' && <p className="text-sm text-status-critical">{errorMessage}</p>}

          <div className="flex justify-end gap-2 border-t border-border-subtle pt-4">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-border bg-surface-2 px-4 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-3"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSaveClick}
              disabled={changes.length === 0 || step === 'saving'}
              className="flex items-center gap-2 rounded-md border border-status-accent/40 bg-status-accent/15 px-4 py-1.5 text-sm font-semibold text-text-primary disabled:cursor-not-allowed disabled:opacity-50 hover:enabled:bg-status-accent/25"
            >
              {step === 'saving' && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
              SAVE POLICY
            </button>
          </div>
        </div>
      )}
    </Modal>
  )
}
