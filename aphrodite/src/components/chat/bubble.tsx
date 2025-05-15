import { cn } from "@/lib/utils";
import { Clipboard, RotateCcw, ThumbsDown, ThumbsUp, UserCircle2 } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { TextShimmerWave } from "./shimmer";
import { toast } from "sonner"
import supabase from "@/common/supabase";
import { useAuth } from "@/hoc/AuthProvider";
import { Chat } from "@/pages/chat/Session";
import { useState } from "react";
import { AlertDialog, AlertDialogAction, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "../ui/alert-dialog";
import { ScrollArea } from "../ui/scroll-area";

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

    const title = doc._source?.metadata?.Judul || "Untitled Document";
    const jenis = doc._source?.metadata?.Jenis || "";
    const nomor = doc._source?.metadata?.Nomor ? `No. ${doc._source?.metadata?.Nomor}` : "";
    const tahun = doc._source?.metadata?.Tahun ? `Tahun ${doc._source?.metadata?.Tahun}` : "";

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

    // Sort references by number for displaying in order
    const sortedReferences = Array.from(references.values())
        .sort((a, b) => a.number - b.number);

    const getPdfUrl = (doc: any): string => {
        if (doc?._source?.files && doc._source.files.length > 0) {
            return "https://peraturan.bpk.go.id" + doc._source.files[0].download_url;
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
                                                let docId = (node?.properties?.href as string).replace("https://chat.lexin.cs.ui.ac.id/details/", "")
                                                if (!docId) return null;
                                                docId = docId.replace("%20", " ")
                                                console.log(docId)
                                                console.log(props?.chat?.documents)
                                                if (typeof props?.chat?.documents === "string") {
                                                    props.chat.documents = JSON.parse(props.chat.documents)
                                                }
                                                const doc = (props.chat.documents as unknown as any[])?.find((doc: any) => doc._id === docId)
                                                if (!references.has(docId)) {
                                                    references.set(docId, {
                                                        number: references.size + 1,
                                                        href: (node?.properties?.href as string),
                                                        doc
                                                    })
                                                    setReferences(new Map(references));
                                                }

                                                console.log(references.get(docId))

                                                return (
                                                    <a rel="noreferrer">
                                                        <AlertDialog>
                                                            <AlertDialogTrigger className="bg-[#192f59] cursor-pointer text-white px-2 no-underline rounded-md hover:opacity-80">{references.get(docId)?.number}</AlertDialogTrigger>
                                                            <AlertDialogContent className="">
                                                                <AlertDialogHeader>
                                                                    <AlertDialogTitle className="text-center text-base prose mb-5">
                                                                        {references.get(docId)?.doc?._source?.metadata?.Judul}
                                                                    </AlertDialogTitle>
                                                                    <AlertDialogDescription className="prose">
                                                                        <ScrollArea className="h-[300px]">
                                                                            {references.get(docId)?.doc?._source?.abstrak?.length > 0 && <b className="!text-center w-full">Abstrak</b>}
                                                                            <ul>{references.get(docId)?.doc?._source?.abstrak?.map((item: string) => <li>{item}</li>)}</ul>
                                                                            {references.get(docId)?.doc?._source?.catatan?.join("\n")}
                                                                            {
                                                                                references.get(docId)?.doc?._source?.files &&
                                                                                <embed
                                                                                    width={"100%"}
                                                                                    height="600"
                                                                                    type="application/pdf"
                                                                                    src={"https://peraturan.bpk.go.id" + references.get(docId)?.doc?._source?.files[0].download_url}
                                                                                />
                                                                            }
                                                                        </ScrollArea>
                                                                        <ul>
                                                                            {references.get(docId)?.doc?._source?.files?.map((item: any) => (
                                                                                <li key={item?.file_id} className="text-sm">
                                                                                    <a href={"https://peraturan.bpk.go.id" + item?.download_url} target="_blank" rel="noreferrer" className="text-[#192f59] hover:underline">
                                                                                        Unduh {item?.filename}
                                                                                    </a>
                                                                                </li>
                                                                            ))}
                                                                        </ul>
                                                                        {references.get(docId)?.doc?._source?.relations &&
                                                                            Object.keys(references.get(docId)?.doc?._source?.relations).map((key: string) => (
                                                                                <div key={key}>
                                                                                    <b>{key}</b>
                                                                                    <ul>
                                                                                        {references.get(docId)?.doc?._source?.relations[key].map((item: any) => (
                                                                                            <li key={item?.file_id} className="text-sm">
                                                                                                <a href={"https://peraturan.bpk.go.id" + item?.url}
                                                                                                    target="_blank" rel="noreferrer"
                                                                                                    className="text-[#192f59] hover:underline">
                                                                                                    {item?.title}
                                                                                                </a>
                                                                                            </li>
                                                                                        ))}
                                                                                    </ul>
                                                                                </div>
                                                                            ))
                                                                        }
                                                                    </AlertDialogDescription>
                                                                </AlertDialogHeader>
                                                                <AlertDialogFooter>
                                                                    <AlertDialogAction>Tutup</AlertDialogAction>
                                                                </AlertDialogFooter>
                                                            </AlertDialogContent>
                                                        </AlertDialog>
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
                                                <div className="grid grid-cols-1 gap-2">
                                                    {sortedReferences.map((ref, index) => (
                                                        <a
                                                            key={index}
                                                            href={getPdfUrl(ref.doc)}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors group"
                                                        >
                                                            <div className="flex-shrink-0 w-6 h-6 rounded-full bg-[#192f59]/10 text-[#192f59] flex items-center justify-center text-xs font-bold">
                                                                {ref.number}
                                                            </div>
                                                            <div className="flex-1 text-sm">
                                                                <p className="font-medium text-[#192f59] leading-tight">
                                                                    {ref.doc?._source?.metadata?.Judul || "Untitled Document"}
                                                                </p>
                                                                <p className="text-xs text-gray-500 mt-1">
                                                                    {formatIEEEReference(ref.doc, ref.number)}
                                                                </p>
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
