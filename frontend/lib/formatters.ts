export function formatIBAN(iban: string | null | undefined): string {
    if (!iban) return '';
    // Remove existing spaces and rejoin with groups of 4
    const cleaned = iban.replace(/\s/g, '');
    return cleaned.replace(/(.{4})/g, '$1 ').trim();
}
