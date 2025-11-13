import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Badge } from "../ui/badge";
import { FileText, Calendar, Shield, Building, ExternalLink, Download, BookOpen, Info } from "lucide-react";

interface DocumentDialogProps {
    docId: string;
    oldDocId?: string;
    references: Map<string, any>;
    getPdfUrl: (doc: any) => string;
    isSuperscript?: boolean;
    citationNumber?: string;
}

export function DocumentDialog({ docId, oldDocId, references, getPdfUrl, isSuperscript, citationNumber }: DocumentDialogProps) {
    // Determine if this is being used in the bottom reference list
    const isBottomReference = citationNumber && !isSuperscript;

    return (
        <Dialog>
            <DialogTrigger className={
                isSuperscript
                    ? "text-blue-600 hover:text-blue-800 cursor-pointer no-underline font-bold text-xs align-super"
                    : isBottomReference
                    ? "text-blue-600 hover:text-blue-800 cursor-pointer no-underline font-bold text-xs"
                    : "bg-[#192f59] cursor-pointer text-white px-2 py-1 no-underline rounded-md hover:opacity-60 opacity-80 transition-opacity font-medium text-xs"
            }>
                {(isSuperscript || isBottomReference) ? citationNumber : (() => {
                    const refDoc = references.get(docId) || references.get(oldDocId || '');
                    const metadata = refDoc?.doc?.source?.metadata;

                    if (!metadata) return docId;

                    const bentukSingkat = metadata["Bentuk Singkat"] || metadata.Jenis || "";
                    const nomor = metadata.Nomor ? `No. ${metadata.Nomor}` : "";
                    const tahun = metadata.Tahun ? `Tahun ${metadata.Tahun}` : "";

                    // Handle special cases like KUH_Perdata
                    if (docId === "KUH_Perdata") {
                        return "Kitab Undang-Undang Hukum Perdata";
                    }
                    if (docId === "UU_1_2023") { // TODO: Remove hardcoding later
                        return "KUHP Terbaru";
                    }

                    // Build display text
                    return [bentukSingkat, nomor, tahun].filter(Boolean).join(" ") || metadata.Judul || docId;
                })()}
            </DialogTrigger>
            <DialogContent className="max-w-5xl w-[96vw] sm:w-[90vw] max-h-[85vh] p-0 overflow-hidden border-gray-200">
                {/* Header */}
                <div className="bg-white border-b border-gray-200 px-3 sm:px-4 py-3 sm:py-4">
                    <DialogHeader>
                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 sm:gap-3">
                            <div className="flex-1 min-w-0">
                                <DialogTitle className="text-left text-base sm:text-lg font-semibold text-gray-900 leading-tight mb-2 pr-2">
                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Judul || "Dokumen Hukum"}
                                </DialogTitle>

                                {/* Key metadata badges */}
                                <div className="flex flex-wrap gap-1">
                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Jenis && (
                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                            <FileText className="w-3 h-3 mr-1" />
                                            <span className="hidden sm:inline">{(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Jenis}</span>
                                            <span className="sm:hidden">{(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Jenis.slice(0, 3)}</span>
                                        </Badge>
                                    )}
                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Nomor && (
                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                            <Building className="w-3 h-3 mr-1" />
                                            No. {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Nomor}
                                        </Badge>
                                    )}
                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Tahun && (
                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                            <Calendar className="w-3 h-3 mr-1" />
                                            {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Tahun}
                                        </Badge>
                                    )}
                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Status && (
                                        <Badge variant="outline" className={`text-xs h-6 ${(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Status === "Berlaku"
                                            ? "border-green-300 text-green-700 bg-green-50"
                                            : "border-amber-300 text-amber-700 bg-amber-50"
                                            }`}>
                                            <Shield className="w-3 h-3 mr-1" />
                                            {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata?.Status}
                                        </Badge>
                                    )}
                                </div>
                            </div>
                        </div>
                    </DialogHeader>
                </div>

                {/* Main content with tabs */}
                <div className="flex-1 overflow-hidden">
                    <Tabs defaultValue="info" className="h-full flex flex-col">
                        <div className="border-b border-gray-200 bg-gray-50 px-3 sm:px-4 py-2">
                            <TabsList className="grid grid-cols-2 w-full bg-white border border-gray-200 h-8">
                                <TabsTrigger value="info" className="flex items-center gap-1 text-xs py-1 data-[state=active]:bg-[#192f59] data-[state=active]:text-white">
                                    <Info className="w-3 h-3" />
                                    Info
                                </TabsTrigger>
                                <TabsTrigger value="document" className="flex items-center gap-1 text-xs py-1 data-[state=active]:bg-[#192f59] data-[state=active]:text-white">
                                    <FileText className="w-3 h-3" />
                                    Dokumen
                                </TabsTrigger>
                            </TabsList>
                        </div>

                        <div className="flex-1 overflow-hidden bg-gray-50">
                            <TabsContent value="info" className="h-full p-0 m-0">
                                <ScrollArea className="h-[45vh] sm:h-[50vh] px-3 sm:px-4 py-3">
                                    <div className="space-y-3 sm:space-y-4">
                                        {/* PDF Download Section */}
                                        {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.files?.length > 0 && (
                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                    <div className="bg-blue-100 p-1.5 rounded-md">
                                                        <Download className="w-4 h-4 text-blue-600" />
                                                    </div>
                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Unduhan PDF</h3>
                                                </div>
                                                <div className="space-y-2">
                                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.files?.map((item: any) => (
                                                        <a
                                                            key={item?.file_id}
                                                            href={"https://peraturan.bpk.go.id" + item?.download_url}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="flex items-center justify-between gap-3 p-3 border border-gray-200 rounded-lg bg-gray-50 hover:bg-gray-100 hover:border-gray-300 transition-all group"
                                                        >
                                                            <div className="flex items-center gap-3">
                                                                <div className="bg-[#192f59] text-white p-2 rounded-md">
                                                                    <FileText className="w-4 h-4" />
                                                                </div>
                                                                <div>
                                                                    <h4 className="font-semibold text-gray-900 group-hover:text-[#192f59] transition-colors text-sm">
                                                                        {item?.filename}
                                                                    </h4>
                                                                    <p className="text-xs text-gray-500">File PDF • Buka di tab baru</p>
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md group-hover:bg-[#192f59] group-hover:text-white group-hover:border-[#192f59] transition-colors">
                                                                <ExternalLink className="w-3 h-3" />
                                                                <span className="font-medium text-xs">Buka</span>
                                                            </div>
                                                        </a>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Relations Section */}
                                        {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.relations && Object.keys((references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.relations).length > 0 && (
                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                <div className="flex items-center gap-2 mb-3 sm:mb-4">
                                                    <div className="bg-green-100 p-1.5 rounded-md">
                                                        <BookOpen className="w-4 h-4 text-green-600" />
                                                    </div>
                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Relasi Dokumen Hukum</h3>
                                                </div>
                                                <div className="space-y-3">
                                                    {Object.entries((references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.relations).map(([relationType, items]) => (
                                                        <div key={relationType} className="border border-gray-200 rounded-lg overflow-hidden bg-gray-50">
                                                            <div className="bg-gradient-to-r from-gray-100 to-gray-50 border-b border-gray-200 px-3 py-2">
                                                                <div className="flex items-center gap-2">
                                                                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                                                                    <h4 className="font-semibold text-sm text-gray-900">{relationType}</h4>
                                                                    <span className="text-xs text-gray-500 bg-white px-2 py-0.5 rounded-full border">
                                                                        {(items as any[]).length} dokumen
                                                                    </span>
                                                                </div>
                                                            </div>
                                                            <div className="divide-y divide-gray-200 max-h-32 overflow-y-auto">
                                                                {(items as any[]).map((item: any, index: number) => (
                                                                    <a
                                                                        key={index}
                                                                        href={"https://peraturan.bpk.go.id" + item?.url}
                                                                        target="_blank"
                                                                        rel="noreferrer"
                                                                        className="flex items-center justify-between p-2 sm:p-3 hover:bg-white transition-colors group bg-gray-50"
                                                                    >
                                                                        <div className="flex items-center gap-2 min-w-0 flex-1">
                                                                            <div className="bg-blue-100 p-1.5 rounded-md flex-shrink-0 group-hover:bg-blue-200 transition-colors">
                                                                                <FileText className="w-3 h-3 text-blue-600" />
                                                                            </div>
                                                                            <div className="min-w-0 flex-1">
                                                                                <span className="text-xs text-gray-900 group-hover:text-[#192f59] transition-colors block truncate font-medium">
                                                                                    {item?.title}
                                                                                </span>
                                                                                <span className="text-xs text-gray-500 block truncate">
                                                                                    Dokumen terkait
                                                                                </span>
                                                                            </div>
                                                                        </div>
                                                                        <ExternalLink className="w-3 h-3 text-gray-400 group-hover:text-[#192f59] transition-colors flex-shrink-0 ml-2" />
                                                                    </a>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Abstract/Summary Card */}
                                        {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.abstrak?.length > 0 && (
                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                    <div className="bg-blue-100 p-1.5 rounded-md">
                                                        <BookOpen className="w-4 h-4 text-blue-600" />
                                                    </div>
                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Ringkasan Dokumen</h3>
                                                </div>
                                                <div className="space-y-2 sm:space-y-3">
                                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.abstrak?.map((item: string, index: number) => (
                                                        <div key={index} className="bg-gray-50 border border-gray-100 rounded-md p-2 sm:p-3">
                                                            <p className="text-gray-700 leading-relaxed text-xs sm:text-sm">
                                                                {item}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Metadata Table */}
                                        <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                            <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                <div className="bg-gray-100 p-1.5 rounded-md">
                                                    <Info className="w-4 h-4 text-gray-600" />
                                                </div>
                                                <h3 className="text-sm sm:text-base font-semibold text-gray-900">Informasi Detail</h3>
                                            </div>
                                            <div className="overflow-x-auto">
                                                <table className="w-full border-collapse border border-gray-200 rounded-md">
                                                    <tbody className="divide-y divide-gray-200">
                                                        {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata && Object.entries((references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.metadata).map(([key, value]) => (
                                                            <tr key={key} className="hover:bg-gray-50 transition-colors">
                                                                <td className="py-2 px-3 text-xs font-medium text-gray-600 bg-gray-50 border-r border-gray-200 w-1/3">
                                                                    {key}
                                                                </td>
                                                                <td className="py-2 px-3 text-xs text-gray-900">
                                                                    {value as string}
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        </div>

                                        {/* Notes/Catatan */}
                                        {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.catatan?.length > 0 && (
                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                    <div className="bg-amber-100 p-1.5 rounded-md">
                                                        <Info className="w-4 h-4 text-amber-600" />
                                                    </div>
                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Catatan Penting</h3>
                                                </div>
                                                <div className="space-y-2">
                                                    {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.catatan?.map((note: string, index: number) => (
                                                        <div key={index} className="flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-md p-2 sm:p-3">
                                                            <div className="w-1.5 h-1.5 bg-amber-500 rounded-full mt-1.5 flex-shrink-0"></div>
                                                            <p className="text-gray-700 text-xs leading-relaxed">
                                                                {note}
                                                            </p>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </ScrollArea>
                            </TabsContent>

                            <TabsContent value="document" className="h-full p-0 m-0">
                                {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.files?.length > 0 ? (
                                    <div className="h-[45vh] sm:h-[50vh] p-3">
                                        <div className="h-full rounded-md overflow-hidden border border-gray-300 bg-gray-100">
                                            <embed
                                                className="w-full h-full"
                                                type="application/pdf"
                                                src={"https://peraturan.bpk.go.id" + (references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.files[0].download_url}
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <div className="h-[45vh] sm:h-[50vh] flex items-center justify-center">
                                        <div className="text-center px-4">
                                            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                                            <p className="text-gray-600 text-sm">Dokumen PDF tidak tersedia</p>
                                        </div>
                                    </div>
                                )}
                            </TabsContent>
                        </div>
                    </Tabs>
                </div>

                {/* Footer */}
                <DialogFooter className="border-t border-gray-200 bg-white px-3 sm:px-4 py-3">
                    <div className="w-full flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                        <div className="text-xs text-gray-500 font-mono">
                            ID: {(references.get(docId) || references.get(oldDocId || ''))?.doc?.id}
                        </div>
                        <div className="flex gap-2">
                            {(references.get(docId) || references.get(oldDocId || ''))?.doc?.source?.files?.length > 0 && (
                                <a
                                    href={getPdfUrl((references.get(docId) || references.get(oldDocId || ''))?.doc)}
                                    target="_blank"
                                    rel="noreferrer"
                                    className="flex items-center gap-2 px-3 py-1.5 bg-[#192f59] text-white rounded-md hover:bg-[#0d1e3f] transition-colors text-xs font-medium"
                                >
                                    <ExternalLink className="w-3 h-3" />
                                    Buka di Tab Baru
                                </a>
                            )}
                        </div>
                    </div>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}