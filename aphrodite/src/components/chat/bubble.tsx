import { cn } from "@/lib/utils";
import { UserCircle2 } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { TextShimmerWave } from "./shimmer";

interface ChatBubbleProps {
    sender: "user" | "assistant";
    timestamp: string;
    isLoading?: boolean;
    isSearching?: boolean;
    isExtracting?: boolean;
    isDone?: boolean;
    message: string;
    context?: string;
}

export default function ChatBubble(props: ChatBubbleProps) {
    const text = (props.sender === "user" || props.isDone) ? props.message : useAnimatedText(props.message);
    const context = (props.sender === "user" || props.isDone) ? props.context : useAnimatedText(props.context || "", "\n");
    let state = "loading";
    if (props.isSearching) {
        state = "searching";
    }
    if (props.isExtracting) {
        state = "extracting";
    }
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
                                    {(props.context) && (
                                        <div className="prose opacity-40 prose-headings:text-base prose-sm max-w-full prose-pre:font-mono prose-code:font-mono">
                                            <Markdown remarkPlugins={[remarkGfm]}>
                                                {context?.split("\n").map((line) => "> " + line.replace("```", "")).join("\n")}
                                            </Markdown>
                                        </div>
                                    )}
                                    <div className="prose prose-headings:text-base prose-sm max-w-full prose-pre:font-mono prose-code:font-mono">
                                        <Markdown remarkPlugins={[remarkGfm]}>
                                            {text}
                                        </Markdown>
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
