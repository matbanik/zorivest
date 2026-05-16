/**
 * TaxDisclaimer — shared disclaimer banner for all tax output surfaces.
 *
 * Per AC-154.16: "This is an estimator, not tax advice. Always consult a CPA."
 * Spec: 06g-gui-tax.md L11, L60
 * MEU: MEU-154
 */

import { TAX_TEST_IDS } from './test-ids'

interface TaxDisclaimerProps {
    className?: string
}

export default function TaxDisclaimer({ className = '' }: TaxDisclaimerProps) {
    return (
        <div
            data-testid={TAX_TEST_IDS.DISCLAIMER}
            role="status"
            className={`px-4 py-2 rounded-md bg-yellow-500/10 border border-yellow-500/20 text-yellow-300 text-xs ${className}`}
        >
            <span aria-hidden="true">⚠️</span> This is an estimator, not tax advice. Always consult a CPA.
        </div>
    )
}
