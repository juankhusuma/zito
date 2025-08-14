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
        // Find all citation links in the message
        const citationRegex = /\[([^\]]+)\]\(https:\/\/chat\.lexin\.cs\.ui\.ac\.id\/details\/([^)]+)\)/g;
        const found: { docId: string, citationNumber: number | null, href: string }[] = [];
        let match;
        while ((match = citationRegex.exec(props.message)) !== null) {
            const docId = match[2].replace("%20", " ");
            // Try to extract number from link text, e.g. "Pasal 13"
            const pasalMatch = match[1].match(/Pasal\s*(\d+)/i);
            const citationNumber = pasalMatch ? parseInt(pasalMatch[1], 10) : null;
            found.push({
                docId,
                citationNumber,
                href: match[0],
            });
        }

        // Build references map ONLY for existing documents
        const newReferences = new Map<string, any>();
        let validIndex = 1;
        for (let i = 0; i < found.length; i++) {
            const item = found[i];
            let docFromProps = null;
            for (const document of props?.chat?.documents as any || []) {
                if (document._id === item.docId && !!document?.source && !document?.pasal) {
                    docFromProps = document;
                    break;
                }
                if (document.id === item.docId && !!document?.source && !document?.pasal) {
                    docFromProps = document;
                    break;
                }
            }
            // Only add if docFromProps exists!
            if (docFromProps) {
                newReferences.set(item.docId, {
                    number: validIndex,
                    href: item.href,
                    doc: docFromProps
                });
                validIndex++;
            }
        }
        setReferences(newReferences);
    }, [props.message, props.chat.documents]);

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
                                                const reference = references.get(docId);

                                                return (
                                                    <Dialog>
                                                        <DialogTrigger className="bg-[#192f59] cursor-pointer text-white px-2 py-1 no-underline rounded-md hover:opacity-80 transition-opacity font-medium text-xs">
                                                            {reference?.number}
                                                        </DialogTrigger>
                                                        {/* ...DialogContent as before... */}
                                                    </Dialog>
                                                );
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
