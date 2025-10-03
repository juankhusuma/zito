/**
 * Utility functions for formatting document references
 */

/**
 * Formats a document reference in IEEE style
 * @param doc - Document object with metadata
 * @param index - Reference index number
 * @returns Formatted IEEE style reference string
 */
export function formatIEEEReference(doc: any, index: number): string {
    if (!doc) return "";
    console.log("Formatting reference for doc:", doc);

    const title = doc.source?.metadata?.Judul || "Untitled Document";
    const jenis = doc.source?.metadata?.Jenis || "";
    const nomor = doc.source?.metadata?.Nomor ? `No. ${doc.source?.metadata?.Nomor}` : "";
    const tahun = doc.source?.metadata?.Tahun ? `Tahun ${doc.source?.metadata?.Tahun}` : "";

    // Construct a more complete IEEE style reference
    return `[${index}] ${jenis} ${nomor} ${tahun}, "${title}."`;
}