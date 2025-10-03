import { cn } from "@/lib/utils";
import { UserCircle2 } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Chat } from "@/pages/chat/Session";
import { useEffect, useState, useRef } from "react";
import { TooltipProvider } from "@radix-ui/react-tooltip";
import { Tooltip, TooltipContent, TooltipTrigger } from "../ui/tooltip";
import { formatIEEEReference } from "@/utils/formatReferences";
import { MessageLoading } from "./MessageLoading";
import { ActionBar } from "./ActionBar";
import { DocumentDialog } from "./DocumentDialog";

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
    thinkingStartTime?: Date;
    finalThinkingDuration?: number;
}

export default function ChatBubble(props: ChatBubbleProps) {
    const animatedText = useAnimatedText(props.message);
    let text = (props.sender === "user" || props.isDone) ? props.message : animatedText;
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
                            <MessageLoading state={state} thinkingStartTime={props.thinkingStartTime} />
                        </div>
                    ) : (
                        props.sender === "user" ? (<p className="prose prose-sm">{text}</p>)
                            : (
                                <div>
                                    {(props.isExtracting) && (
                                        <MessageLoading state={state} thinkingStartTime={props.thinkingStartTime} />
                                    )}
                                    <div className={cn("prose prose-headings:text-base prose-sm max-w-full prose-pre:font-mono prose-code:font-mono",
                                        props.isError && "text-red-700"
                                    )}>
                                        <Markdown remarkPlugins={[remarkGfm]} components={{
                                            a: ({ node, children }) => {
                                                const href = node?.properties?.href as string;
                                                
                                                // Handle non-citation links (fallback to regular link)
                                                if (!href || !href.includes("chat.lexin.cs.ui.ac.id/details/")) {
                                                    return <a href={href} target="_blank" rel="noreferrer" className="text-blue-600 hover:text-blue-800 underline">{children}</a>;
                                                }
                                                
                                                let docId = href.replace("https://chat.lexin.cs.ui.ac.id/details/", "");
                                                if (!docId) return null;
                                                docId = docId.replace("%20", " ");
                                                docId = docId.replace(/tahun_/ig, "");
                                                docId = docId.replace("__", "_");
                                                let oldDocId = docId
                                                // replace the number in the middle if its only 1 digit add a leading 0, like UU_1_2023 -> UU_01_2023
                                                docId = docId.replace(/_(\d{1})_/g, "_0$1_");
                                                if (typeof props?.chat?.documents === "string") {
                                                    props.chat.documents = JSON.parse(props.chat.documents)
                                                }
                                                // if oldDocId contains a number in the middle, remove the leading zero if it exists
                                                if (oldDocId.split("_").length === 3 && oldDocId.split("_")[1].length === 2) {
                                                    oldDocId = oldDocId.replace(/_0+([1-9]\d*)_/g, "_$1_");
                                                }
                                                // Generate more possible ID variations for better matching
                                                const possibleIds = new Set([
                                                    docId,
                                                    oldDocId,
                                                    docId.replace(/_0+(\d+)_/g, "_$1_"), // Remove leading zeros: UU_05_2023 -> UU_5_2023  
                                                    docId.replace(/_(\d{1})_/g, "_0$1_"), // Add leading zeros: UU_5_2023 -> UU_05_2023
                                                    (node?.properties?.href as string).replace("https://chat.lexin.cs.ui.ac.id/details/", "") // Original URL-encoded version
                                                ]);

                                                let doc = null;

                                                for (const document of props?.chat?.documents as any || []) {
                                                    const documentId = document._id || document.id;
                                                    
                                                    // Check against all possible ID variations
                                                    for (const possibleId of possibleIds) {
                                                        if (documentId === possibleId && !!document?.source && !document?.pasal) {
                                                            doc = document;
                                                            break;
                                                        }
                                                    }
                                                    
                                                    if (doc) break; // Exit outer loop if found
                                                }

                                                if (!references.has(docId) && doc && doc.source && !references.has(oldDocId)) {
                                                    const newReferences = new Map(references);
                                                    newReferences.set(docId, {
                                                        number: newReferences.size + 1,
                                                        href: (node?.properties?.href as string),
                                                        doc
                                                    });
                                                    setReferences(newReferences);
                                                }

                                                // Memoized fetch: only fetch if not already fetched
                                                if (!doc && !fetchedIds.current.has(docId) && !fetchedIds.current.has(oldDocId) && !references.has(docId) && !references.has(oldDocId)) {
                                                    fetchedIds.current.add(docId);
                                                    fetchedIds.current.add(oldDocId);
                                                    
                                                    // Special handling for common documents
                                                    if (docId === "KUH_Perdata") {
                                                        const newReferences = new Map(references);
                                                        newReferences.set(docId, {
                                                            number: newReferences.size + 1,
                                                            href: href,
                                                            doc: {
                                                                _id: "KUH_Perdata",
                                                                source: {
                                                                    metadata: {
                                                                        Judul: "Kitab Undang-Undang Hukum Perdata",
                                                                        "Bentuk Singkat": "KUH Perdata",
                                                                        Jenis: "Kitab Undang-Undang"
                                                                    }
                                                                }
                                                            }
                                                        });
                                                        setReferences(newReferences);
                                                    }
                                                    
                                                    if (docId.split("_").length !== 3) {
                                                        // Create minimal reference instead of returning early
                                                        const newReferences = new Map(references);
                                                        newReferences.set(docId, {
                                                            number: newReferences.size + 1,
                                                            href: href,
                                                            doc: {
                                                                _id: docId,
                                                                source: {
                                                                    metadata: {
                                                                        Judul: children as string || docId,
                                                                        "Bentuk Singkat": docId
                                                                    }
                                                                }
                                                            }
                                                        });
                                                        setReferences(newReferences);
                                                        // Continue to Dialog rendering below, don't return early
                                                    } else {
                                                        fetch(`https://chat.lexin.cs.ui.ac.id/elasticsearch/peraturan_indonesia/_search`, {
                                                        method: "POST",
                                                        headers: {
                                                            "Content-Type": "application/json",
                                                            "Authorization": `Basic ${btoa(`elastic:password`)}`
                                                        },
                                                        body: JSON.stringify({
                                                            query: {
                                                                bool: {
                                                                    should: Array.from(possibleIds).map(id => ({
                                                                        match: { _id: id }
                                                                    }))
                                                                }
                                                            }
                                                        })
                                                    }).then(async (res) => {
                                                        if (!res.ok) return;
                                                        
                                                        const data = await res.json();
                                                        if (data.hits && data.hits.hits && data.hits.hits.length > 0) {
                                                            const d = data.hits.hits[0];
                                                            doc = {
                                                                _id: d._id,
                                                                id: d._id,
                                                                source: d._source,
                                                                pasal: d._source.pasal || null
                                                            };
                                                            if (doc && doc.source) {
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
                                                                setReferences(newReferences);
                                                            }
                                                        }
                                                    }).catch((error) => {
                                                        console.warn(`Failed to fetch document ${docId}:`, error.message);
                                                    });
                                                    }
                                                }

                                                // If we have minimal reference data, create a minimal doc object to proceed
                                                if (!doc || !doc.source) {
                                                    const refDoc = references.get(docId) || references.get(oldDocId);
                                                    if (refDoc?.doc) {
                                                        doc = refDoc.doc;
                                                    } else {
                                                        // Create minimal doc structure for rendering
                                                        doc = {
                                                            _id: docId,
                                                            source: {
                                                                metadata: {
                                                                    Judul: children as string || docId,
                                                                    "Bentuk Singkat": docId
                                                                }
                                                            }
                                                        };
                                                    }
                                                }

                                                // For documents without metadata, try to create minimal reference info
                                                const refDoc = references.get(docId) || references.get(oldDocId);
                                                if (!refDoc?.doc?.source?.metadata) {
                                                    // Create minimal reference for documents like KUH_Perdata
                                                    const newReferences = new Map(references);
                                                    newReferences.set(docId, {
                                                        number: newReferences.size + 1,
                                                        href: (node?.properties?.href as string),
                                                        doc: {
                                                            ...doc,
                                                            source: {
                                                                ...doc.source,
                                                                metadata: {
                                                                    ...doc.source.metadata,
                                                                    Judul: doc.source.metadata?.Judul || docId,
                                                                    "Bentuk Singkat": doc.source.metadata?.["Bentuk Singkat"] || docId
                                                                }
                                                            }
                                                        }
                                                    });
                                                    setReferences(newReferences);
                                                }

                                                return (
                                                    <a rel="noreferrer">
                                                        <DocumentDialog
                                                            docId={docId}
                                                            oldDocId={oldDocId}
                                                            references={references}
                                                            getPdfUrl={getPdfUrl}
                                                        />
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

                                        <ActionBar chat={props.chat} messageId={props.messageId} sessionId={props.sessionId} text={text} history={props.history} finalThinkingDuration={props.finalThinkingDuration} />
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