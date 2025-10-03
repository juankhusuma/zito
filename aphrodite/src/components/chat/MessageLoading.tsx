import { useTimer } from "@/hooks/useTimer";
import { TextShimmerWave } from "./shimmer";

interface MessageLoadingProps {
    state: string;
    thinkingStartTime?: Date;
}

export function MessageLoading({ state, thinkingStartTime }: MessageLoadingProps) {
    const { elapsedTime, formatTime } = useTimer(
        thinkingStartTime,
        state === "loading" || state === "searching" || state === "extracting"
    );

    const getLoadingText = () => {
        const timeDisplay = thinkingStartTime ? ` (${formatTime(elapsedTime)})` : '';

        switch (state) {
            case "searching":
                return `Mencari Undang-Undang dan Peraturan yang relevan...${timeDisplay}`;
            case "extracting":
                return `Menganalisa hasil pencarian...${timeDisplay}`;
            default:
                return `Sedang berpikir...${timeDisplay}`;
        }
    };

    if (state === "searching" || state === "extracting" || (state === "loading" && thinkingStartTime)) {
        return (
            <TextShimmerWave
                className='[--base-color:#0f5a9c] [--base-gradient-color:#192f59] text-sm'
                duration={0.75}
                spread={1}
                zDistance={1}
                scaleDistance={1.01}
                rotateYDistance={10}
            >
                {getLoadingText()}
            </TextShimmerWave>
        );
    }

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