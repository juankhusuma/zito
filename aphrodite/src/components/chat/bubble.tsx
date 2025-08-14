import { cn } from "@/lib/utils";
import { Clipboard, RotateCcw, ThumbsDown, ThumbsUp, UserCircle2, FileText, Calendar, Shield, Building, ExternalLink, Download, BookOpen, Info } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { TextShimmerWave } from "./shimmer";
import { toast } from "sonner"
import supabase from "@/common/supabase";
import { useAuth } from "@/hoc/AuthProvider";
import { Chat } from "@/pages/chat/Session";
import { useEffect, useState, useRef } from "react";
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "../ui/dialog";
import { ScrollArea } from "../ui/scroll-area";
import { TooltipProvider } from "@radix-ui/react-tooltip";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { Badge } from "../ui/badge";

interface ChatBubbleProps {
    sender: "user" | "assistant";
    chat: Chat;
    timestamp: string;
    isLoading?: boolean;
    isSearching?: boolean;
    isExtracting?: boolean;
    isError?: boolean;
    isDone?: boolean;
    message: string;
    context?: string;
    history: any[];
    sessionId: string;
    messageId: string;
}

function ActionBar(props: { text: string, history: any[], sessionId: string, messageId: string, chat: Chat }) {
    const { user } = useAuth();
    const [isLiked, setIsLiked] = useState(!!props.chat.is_liked);
    const [isDisliked, setIsDisliked] = useState(!!props.chat.is_disliked);
    return (
        <div className="flex items-center gap-3">
            <ThumbsUp onClick={() => {
                setIsLiked(true);
                setIsDisliked(false);
                supabase.from("chat").update({
                    is_liked: true,
                    is_disliked: false
                }).eq("id", props.messageId).then(() => {
                    toast("Upvoted the result")
                })
            }} size={15} color="#192f59" className={cn("cursor-pointer transition-all",
                isLiked ? "fill-[#192f59] hover:fill-none" : "hover:fill-[#192f59] hover:opacity-80"
            )} />
            <ThumbsDown onClick={() => {
                setIsDisliked(true);
                setIsLiked(false);
                supabase.from("chat").update({
                    is_liked: false,
                    is_disliked: true
                }).eq("id", props.messageId).then(() => {
                    toast("Downvoted the result")
                })
            }} size={15} color="#192f59" className={cn("cursor-pointer transition-all",
                isDisliked ? "fill-[#192f59] hover:fill-none" : "hover:opacity-80"
            )} />
            <RotateCcw onClick={async () => {
                const lastMessage = props.history[props.history.length - 1];
                await supabase.from("chat").delete().eq("id", lastMessage.id);
                const { data } = await supabase.auth.getSession()
                if (!data.session) {
                    console.error("No session found")
                    return
                }
                await fetch(`${import.meta.env.VITE_API_URL}/api/v1/chat`, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        session_uid: props.sessionId,
                        user_uid: user?.id,
                        access_token: data?.session?.access_token,
                        refresh_token: data?.session?.refresh_token,
                        messages: [...props.history?.map((chat) => ({
                            content: chat.content,
                            role: chat.role,
                            timestamp: chat.created_at
                        }))]
                    })
                })
                toast("Regenerating response");
            }} size={15} color="#192f59" className="cursor-pointer transition-all" />
            <Clipboard onClick={() => {
                toast("Copied to clipboard")
                navigator.clipboard.writeText(props.text);
            }} size={15} color="#192f59" className="hover:fill-[#192f59] cursor-pointer transition-all" />
        </div>
    )
}

function formatIEEEReference(doc: any, index: number): string {
    if (!doc) return "";
    console.log("Formatting reference for doc:", doc);

    const title = doc.source?.metadata?.Judul || "Untitled Document";
    const jenis = doc.source?.metadata?.Jenis || "";
    const nomor = doc.source?.metadata?.Nomor ? `No. ${doc.source?.metadata?.Nomor}` : "";
    const tahun = doc.source?.metadata?.Tahun ? `Tahun ${doc.source?.metadata?.Tahun}` : "";

    // Construct a more complete IEEE style reference
    return `[${index}] ${jenis} ${nomor} ${tahun}, "${title}."`;
}

export default function ChatBubble(props: ChatBubbleProps) {
    const animatedText = useAnimatedText(props.message);
    const text = (props.sender === "user" || props.isDone) ? props.message : animatedText;

    let state = "loading";
    if (props.isSearching) {
        state = "searching";
    }
    if (props.isExtracting) {
        state = "extracting";
    }
    const [references, setReferences] = useState<Map<string, any>>(new Map());
    const [sortedReferences, setSortedReferences] = useState<any[]>(Array.from(references.values())
        .sort((a, b) => a.number - b.number));
    const fetchedIds = useRef<Set<string>>(new Set());

    useEffect(() => {
        const sorted = Array.from(references.values()).sort((a, b) => a.number - b.number);
        setSortedReferences(sorted);
    }
        , [references]);

    const getPdfUrl = (doc: any): string => {
        if (doc?.source?.files && doc.source.files.length > 0) {
            return "https://peraturan.bpk.go.id" + doc.source.files[0].download_url;
        }
        return "#";
    };

    return (
        <div className={cn("flex mb-3 text-xs lg:text-sm", props.sender === "user" ? "flex-row" : "flex-row-reverse")}>
            <div className={cn("flex items-start w-full", props.sender === "user" ? "justify-end" : "justify-start")}>
                {props.sender === "assistant" && <img src="/lexin-logo.svg" alt="lexin" className={cn(
                    "w-[20px] h-[20px] object-contain object-center mt-2",
                    !props.isDone || props.isLoading ? "animate-pulse" : ""
                )} />}
                <div
                    className={cn(
                        "rounded-lg px-3 py-2 w-fit",
                        props.sender === "assistant" ? "text-primary-foreground ml-2" : "bg-muted border-1 mr-2 max-w-1/2"
                    )}
                >
                    {(props.isLoading || props.isSearching) ? (
                        <div className="flex items-center space-x-2">
                            <MessageLoading state={state} />
                        </div>
                    ) : (
                        props.sender === "user" ? (<p className="prose prose-sm">{text}</p>)
                            : (
                                <div>
                                    {(props.isExtracting) && (
                                        <MessageLoading state={state} />
                                    )}
                                    <div className={cn("prose prose-headings:text-base prose-sm max-w-full prose-pre:font-mono prose-code:font-mono",
                                        props.isError && "text-red-700"
                                    )}>
                                        <Markdown remarkPlugins={[remarkGfm]} components={{
                                            a: ({ node }) => {
                                                let docId = (node?.properties?.href as string).replace("https://chat.lexin.cs.ui.ac.id/details/", "");
                                                if (!docId) return null;
                                                docId = docId.replace("%20", " ");
                                                docId = docId.replace(/tahun_/ig, "");
                                                docId = docId.replace("__", "_");
                                                // replace the number in the middle if its only 1 digit add a leading 0, like UU_1_2023 -> UU_01_2023
                                                docId = docId.replace(/_(\d{1})_/g, "_0$1_");
                                                if (typeof props?.chat?.documents === "string") {
                                                    props.chat.documents = JSON.parse(props.chat.documents)
                                                }
                                                let doc = null;
                                                for (const document of props?.chat?.documents as any || []) {
                                                    if (document._id === docId && !!document?.source && !document?.pasal) {
                                                        doc = document;
                                                        break;
                                                    }
                                                    if (document.id === docId && !!document?.source && !document?.pasal) {
                                                        doc = document;
                                                        break;
                                                    }
                                                }

                                                if (!references.has(docId) && doc && doc.source) {
                                                    const newReferences = new Map(references);
                                                    newReferences.set(docId, {
                                                        number: newReferences.size + 1,
                                                        href: (node?.properties?.href as string),
                                                        doc
                                                    });
                                                    setReferences(newReferences);
                                                }

                                                // Memoized fetch: only fetch if not already fetched
                                                if (!doc && !fetchedIds.current.has(docId)) {
                                                    fetchedIds.current.add(docId);
                                                    if (docId.split("_").length !== 3) {
                                                        console.warn("Invalid document ID format:", docId);
                                                        return <></>;
                                                    }
                                                    fetch(`https://chat.lexin.cs.ui.ac.id/elasticsearch/peraturan_indonesia/_search`, {
                                                        method: "POST",
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            "Authorization": `Basic ${btoa(`elastic:password`)}`
                                                        },
                                                        body: JSON.stringify({
                                                            query: {
                                                                match: {
                                                                    _id: docId
                                                                }
                                                            }
                                                        })
                                                    }).then(async (res) => {
                                                        if (!res.ok) {
                                                            console.error("Failed to fetch document:", res.statusText);
                                                            return;
                                                        }
                                                        const data = await res.json();
                                                        if (data.hits && data.hits.hits && data.hits.hits.length > 0) {
                                                            const d = data.hits.hits[0];
                                                            doc = {
                                                                _id: d._id,
                                                                id: d._id,
                                                                source: d._source,
                                                                pasal: d._source.pasal || null
                                                            };
                                                            if (!doc || !doc.source) {
                                                                console.warn("No source found for document ID:", docId);
                                                                return <></>;
                                                            }
                                                            if (!props?.chat?.documents) {
                                                                props.chat.documents = [] as any;
                                                            }
                                                            (props?.chat?.documents as any)?.push(doc);
                                                            const newReferences = new Map(references);
                                                            newReferences.set(docId, {
                                                                number: newReferences.size + 1,
                                                                href: (node?.properties?.href as string),
                                                                doc
                                                            });
                                                            console.log("Saved document:", doc);
                                                            setReferences(newReferences);
                                                        } else {
                                                            console.warn("No document found for ID:", docId);
                                                        }
                                                    }).catch((error) => {
                                                        console.error("Error fetching document:", error);
                                                    });
                                                }

                                                if (!doc || !doc.source || !references.get(docId)?.doc?.source?.metadata?.Nomor) {
                                                    console.warn("No source found for document ID:", docId);
                                                    return <></>;
                                                }

                                                return (
                                                    <a rel="noreferrer">
                                                        <Dialog>
                                                            <DialogTrigger className="bg-[#192f59] cursor-pointer text-white px-2 py-1 no-underline rounded-md hover:opacity-60 opacity-80 transition-opacity font-medium text-xs">
                                                                [{references.get(docId)?.number}] {references.get(docId)?.doc?.source?.metadata?.["Bentuk Singkat"]} No. {references.get(docId)?.doc?.source?.metadata?.["Nomor"]} Tahun {references.get(docId)?.doc?.source?.metadata?.["Tahun"]}
                                                            </DialogTrigger>
                                                            <DialogContent className="max-w-5xl w-[96vw] sm:w-[90vw] max-h-[85vh] p-0 overflow-hidden border-gray-200">
                                                                {/* Header */}
                                                                <div className="bg-white border-b border-gray-200 px-3 sm:px-4 py-3 sm:py-4">
                                                                    <DialogHeader>
                                                                        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 sm:gap-3">
                                                                            <div className="flex-1 min-w-0">
                                                                                <DialogTitle className="text-left text-base sm:text-lg font-semibold text-gray-900 leading-tight mb-2 pr-2">
                                                                                    {references.get(docId)?.doc?.source?.metadata?.Judul || "Dokumen Hukum"}
                                                                                </DialogTitle>

                                                                                {/* Key metadata badges */}
                                                                                <div className="flex flex-wrap gap-1">
                                                                                    {references.get(docId)?.doc?.source?.metadata?.Jenis && (
                                                                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                                                                            <FileText className="w-3 h-3 mr-1" />
                                                                                            <span className="hidden sm:inline">{references.get(docId)?.doc?.source?.metadata?.Jenis}</span>
                                                                                            <span className="sm:hidden">{references.get(docId)?.doc?.source?.metadata?.Jenis.slice(0, 3)}</span>
                                                                                        </Badge>
                                                                                    )}
                                                                                    {references.get(docId)?.doc?.source?.metadata?.Nomor && (
                                                                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                                                                            <Building className="w-3 h-3 mr-1" />
                                                                                            No. {references.get(docId)?.doc?.source?.metadata?.Nomor}
                                                                                        </Badge>
                                                                                    )}
                                                                                    {references.get(docId)?.doc?.source?.metadata?.Tahun && (
                                                                                        <Badge variant="outline" className="border-gray-300 text-gray-700 bg-gray-50 text-xs h-6">
                                                                                            <Calendar className="w-3 h-3 mr-1" />
                                                                                            {references.get(docId)?.doc?.source?.metadata?.Tahun}
                                                                                        </Badge>
                                                                                    )}
                                                                                    {references.get(docId)?.doc?.source?.metadata?.Status && (
                                                                                        <Badge variant="outline" className={`text-xs h-6 ${references.get(docId)?.doc?.source?.metadata?.Status === "Berlaku"
                                                                                            ? "border-green-300 text-green-700 bg-green-50"
                                                                                            : "border-amber-300 text-amber-700 bg-amber-50"
                                                                                            }`}>
                                                                                            <Shield className="w-3 h-3 mr-1" />
                                                                                            {references.get(docId)?.doc?.source?.metadata?.Status}
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
                                                                                        {references.get(docId)?.doc?.source?.files?.length > 0 && (
                                                                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                                                                    <div className="bg-blue-100 p-1.5 rounded-md">
                                                                                                        <Download className="w-4 h-4 text-blue-600" />
                                                                                                    </div>
                                                                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Unduhan PDF</h3>
                                                                                                </div>
                                                                                                <div className="space-y-2">
                                                                                                    {references.get(docId)?.doc?.source?.files?.map((item: any) => (
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

                                                                                        {/* Relations Section - Enhanced */}
                                                                                        {references.get(docId)?.doc?.source?.relations && Object.keys(references.get(docId)?.doc?.source?.relations).length > 0 && (
                                                                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                                                                <div className="flex items-center gap-2 mb-3 sm:mb-4">
                                                                                                    <div className="bg-green-100 p-1.5 rounded-md">
                                                                                                        <BookOpen className="w-4 h-4 text-green-600" />
                                                                                                    </div>
                                                                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Relasi Dokumen Hukum</h3>
                                                                                                </div>
                                                                                                <div className="space-y-3">
                                                                                                    {Object.entries(references.get(docId)?.doc?.source?.relations).map(([relationType, items]) => (
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
                                                                                        {references.get(docId)?.doc?.source?.abstrak?.length > 0 && (
                                                                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                                                                    <div className="bg-blue-100 p-1.5 rounded-md">
                                                                                                        <BookOpen className="w-4 h-4 text-blue-600" />
                                                                                                    </div>
                                                                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Ringkasan Dokumen</h3>
                                                                                                </div>
                                                                                                <div className="space-y-2 sm:space-y-3">
                                                                                                    {references.get(docId)?.doc?.source?.abstrak?.map((item: string, index: number) => (
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
                                                                                                        {references.get(docId)?.doc?.source?.metadata && Object.entries(references.get(docId)?.doc?.source?.metadata).map(([key, value]) => (
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
                                                                                        {references.get(docId)?.doc?.source?.catatan?.length > 0 && (
                                                                                            <div className="bg-white border border-gray-200 rounded-lg p-3 sm:p-4">
                                                                                                <div className="flex items-center gap-2 mb-2 sm:mb-3">
                                                                                                    <div className="bg-amber-100 p-1.5 rounded-md">
                                                                                                        <Info className="w-4 h-4 text-amber-600" />
                                                                                                    </div>
                                                                                                    <h3 className="text-sm sm:text-base font-semibold text-gray-900">Catatan Penting</h3>
                                                                                                </div>
                                                                                                <div className="space-y-2">
                                                                                                    {references.get(docId)?.doc?.source?.catatan?.map((note: string, index: number) => (
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
                                                                                {references.get(docId)?.doc?.source?.files?.length > 0 ? (
                                                                                    <div className="h-[45vh] sm:h-[50vh] p-3">
                                                                                        <div className="h-full rounded-md overflow-hidden border border-gray-300 bg-gray-100">
                                                                                            <embed
                                                                                                className="w-full h-full"
                                                                                                type="application/pdf"
                                                                                                src={"https://peraturan.bpk.go.id" + references.get(docId)?.doc?.source?.files[0].download_url}
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
                                                                            ID: {references.get(docId)?.doc?.id}
                                                                        </div>
                                                                        <div className="flex gap-2">
                                                                            {references.get(docId)?.doc?.source?.files?.length > 0 && (
                                                                                <a
                                                                                    href={getPdfUrl(references.get(docId)?.doc)}
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
                                                    </a>
                                                )
                                            },
                                        }}>
                                            {text.replace("```", "").replace(/\]\(([^)]+)\)/g, (_, url) => {
                                                // Replace spaces with %20 in URLs
                                                const encodedUrl = url.replace(/ /g, '%20');
                                                return `](${encodedUrl})`;
                                            })}
                                        </Markdown>

                                        {/* Reference List with Improved Styling */}
                                        {props.sender === "assistant" && sortedReferences.length > 0 && (
                                            <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                                                <h4 className="font-semibold text-sm flex items-center gap-2 mb-3 text-[#192f59]">
                                                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-book-marked">
                                                        <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                                                        <polyline points="10 2 10 10 13 7 16 10 16 2"></polyline>
                                                    </svg>
                                                    Sumber Referensi
                                                </h4>
                                                <div className="grid grid-cols-1 gap-2 mb-5">
                                                    <TooltipProvider>

                                                        {sortedReferences.map((ref, index) => (
                                                            <a
                                                                key={index}
                                                                href={getPdfUrl(ref.doc)}
                                                                target="_blank"
                                                                rel="noreferrer"
                                                                className="flex items-center gap-3 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group"
                                                            >
                                                                <div className="flex-1 text-sm">
                                                                    <Tooltip>
                                                                        <div className="text-xs text-gray-500 mt-1 cursor-pointer">
                                                                            <TooltipTrigger className="text-left">
                                                                                {formatIEEEReference(ref.doc, ref.number)}
                                                                            </TooltipTrigger>
                                                                        </div>
                                                                        <TooltipContent className="max-w-md">
                                                                            {ref.doc?.source?.metadata?.Judul || "Untitled Document"}
                                                                        </TooltipContent>
                                                                    </Tooltip>
                                                                </div>
                                                                <div className="flex-shrink-0 text-[#192f59] opacity-0 group-hover:opacity-100 transition-opacity">
                                                                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-external-link">
                                                                        <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                                                                        <polyline points="15 3 21 3 21 9"></polyline>
                                                                        <line x1="10" y1="14" x2="21" y2="3"></line>
                                                                    </svg>
                                                                </div>
                                                            </a>
                                                        ))}
                                                    </TooltipProvider>
                                                </div>
                                            </div>
                                        )}

                                        <ActionBar chat={props.chat} messageId={props.messageId} sessionId={props.sessionId} text={text} history={props.history} />
                                    </div>
                                </div>
                            )
                    )}
                </div>
                {props.sender === "user" && <UserCircle2 className="text-sm font-light mt-2 text-gray-600" />}
            </div>
        </div>
    )
}

function MessageLoading({ state }: {
    state: string
}) {
    if (state === "searching") return (
        <TextShimmerWave
            className='[--base-color:#0f5a9c] [--base-gradient-color:#192f59] text-sm'
            duration={0.75}
            spread={1}
            zDistance={1}
            scaleDistance={1.01}
            rotateYDistance={10}
        >
            Mencari Undang-Undang dan Peraturan yang relevan...
        </TextShimmerWave>
    )


    if (state === "extracting") return (
        <TextShimmerWave
            className='[--base-color:#0f5a9c] [--base-gradient-color:#192f59] text-sm'
            duration={0.75}
            spread={1}
            zDistance={1}
            scaleDistance={1.01}
            rotateYDistance={10}
        >
            Menganalisa hasil pencarian...
        </TextShimmerWave>
    )

    return (
        <svg
            width="24"
            height="24"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
            className="text-[#192f59]"
        >
            <circle cx="4" cy="12" r="2" fill="currentColor">
                <animate
                    id="spinner_qFRN"
                    begin="0;spinner_OcgL.end+0.25s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
            <circle cx="12" cy="12" r="2" fill="currentColor">
                <animate
                    begin="spinner_qFRN.begin+0.1s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
            <circle cx="20" cy="12" r="2" fill="currentColor">
                <animate
                    id="spinner_OcgL"
                    begin="spinner_qFRN.begin+0.2s"
                    attributeName="cy"
                    calcMode="spline"
                    dur="0.6s"
                    values="12;6;12"
                    keySplines=".33,.66,.66,1;.33,0,.66,.33"
                />
            </circle>
        </svg>
    );
}
