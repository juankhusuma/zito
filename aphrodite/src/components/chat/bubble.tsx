import { cn } from "@/lib/utils";
import { UserCircle2 } from "lucide-react";
import { useAnimatedText } from "../ui/animated-text";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Chat } from "@/pages/chat/Session";
import { useEffect, useState, useRef } from "react";
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
  let text =
    props.sender === "user" || props.isDone ? props.message : animatedText;
  let state = "loading";
  if (props.isSearching) {
    state = "searching";
  }
  if (props.isExtracting) {
    state = "extracting";
  }
  const [references, setReferences] = useState<Map<string, any>>(new Map());
  const [sortedReferences, setSortedReferences] = useState<any[]>([]);
  const fetchedIds = useRef<Set<string>>(new Set());

  const dedupeParagraphCitations = (content: string): string => {
    const paragraphs = content.split(/\n{2,}/);
    const citationRegex =
      /\[\[(\d+)\]\]\(https:\/\/chat\.lexin\.cs\.ui\.ac\.id\/details\/([^\)\s]+)\)/g;

    const dedupedParagraphs = paragraphs.map((paragraph) => {
      const seenDocIds = new Set<string>();
      return paragraph.replace(citationRegex, (match, _num, docId) => {
        if (seenDocIds.has(docId)) {
          return "";
        }
        seenDocIds.add(docId);
        return match;
      });
    });

    return dedupedParagraphs.join("\n\n");
  };

  useEffect(() => {
    // If backend provides canonical citations, prefer those for the reference panel
    if (
      props.sender === "assistant" &&
      Array.isArray(props.chat.citations) &&
      props.chat.citations.length > 0
    ) {
      const canonical = props.chat.citations
        .filter((c) => c && typeof c.number === "number")
        .sort((a, b) => a.number - b.number)
        .map((c) => ({
          number: c.number,
          href: `https://chat.lexin.cs.ui.ac.id/details/${c.doc_id}`,
          doc: {
            _id: c.doc_id,
            id: c.doc_id,
            source: {
              metadata: {
                Judul: c.title || c.doc_id,
                "Bentuk Singkat": undefined,
              },
            },
          },
        }));
      setSortedReferences(canonical);
      return;
    }

    // Fallback: derive references from inline links as before
    const derived = Array.from(references.values()).sort(
      (a, b) => a.number - b.number
    );
    setSortedReferences(derived);
  }, [references, props.sender, props.chat.citations]);

  const getPdfUrl = (doc: any): string => {
    if (doc?.source?.files && doc.source.files.length > 0) {
      return "https://peraturan.bpk.go.id" + doc.source.files[0].download_url;
    }
    return "#";
  };

  const stripLlmReferenceSection = (content: string): string => {
    // Regex to match "## Referensi" or similar headings at the end of the text
    // and everything that follows it
    const refHeadingRegex = /\n+#+\s*Referensi[\s\S]*$/i;
    return content.replace(refHeadingRegex, "");
  };

  // Apply stripping first, then dedupe citations in the remaining text
  const cleanedText = dedupeParagraphCitations(stripLlmReferenceSection(text));

  return (
    <div
      className={cn(
        "flex mb-3 text-xs lg:text-sm",
        props.sender === "user" ? "flex-row" : "flex-row-reverse"
      )}
    >
      <div
        className={cn(
          "flex items-start w-full",
          props.sender === "user" ? "justify-end" : "justify-start"
        )}
      >
        {props.sender === "assistant" && (
          <img
            src="/lexin-logo.svg"
            alt="lexin"
            className={cn(
              "w-[20px] h-[20px] object-contain object-center mt-2",
              !props.isDone || props.isLoading ? "animate-pulse" : ""
            )}
          />
        )}
        <div
          className={cn(
            "rounded-lg px-3 py-2 w-fit",
            props.sender === "assistant"
              ? "text-primary-foreground ml-2"
              : "bg-muted border-1 mr-2 max-w-1/2"
          )}
        >
          {props.isLoading || props.isSearching ? (
            <div className="flex items-center space-x-2">
              <MessageLoading
                state={state}
                thinkingStartTime={props.thinkingStartTime}
              />
            </div>
          ) : props.sender === "user" ? (
            <p className="prose prose-sm">{text}</p>
          ) : (
            <div>
              {props.isExtracting && (
                <MessageLoading
                  state={state}
                  thinkingStartTime={props.thinkingStartTime}
                />
              )}
              <div
                className={cn(
                  "prose prose-headings:text-base prose-sm max-w-full prose-pre:font-mono prose-code:font-mono",
                  props.isError && "text-red-700"
                )}
              >
                <Markdown
                  remarkPlugins={[remarkGfm]}
                  components={{
                    a: ({ node, children }) => {
                      const href = node?.properties?.href as string;

                      // Check if this is a numbered citation like [1], [2], etc.
                      const childText = Array.isArray(children)
                        ? children[0]
                        : children;
                      const isCitation =
                        typeof childText === "string" &&
                        /^\[\d+\]$/.test(childText as string);

                      // Handle non-citation, non-details links (regular external link)
                      if (
                        !href ||
                        !href.includes("chat.lexin.cs.ui.ac.id/details/")
                      ) {
                        return (
                          <a
                            href={href}
                            target="_blank"
                            rel="noreferrer"
                            className="text-blue-600 hover:text-blue-800 underline"
                          >
                            {children}
                          </a>
                        );
                      }

                      let docId = href.replace(
                        "https://chat.lexin.cs.ui.ac.id/details/",
                        ""
                      );
                      if (!docId) return null;
                      docId = docId.replace("%20", " ");
                      docId = docId.replace(/tahun_/gi, "");
                      docId = docId.replace("__", "_");
                      let oldDocId = docId;
                      // replace the number in the middle if its only 1 digit add a leading 0, like UU_1_2023 -> UU_01_2023
                      docId = docId.replace(/_(\d{1})_/g, "_0$1_");
                      if (typeof props?.chat?.documents === "string") {
                        props.chat.documents = JSON.parse(props.chat.documents);
                      }
                      // if oldDocId contains a number in the middle, remove the leading zero if it exists
                      if (
                        oldDocId.split("_").length === 3 &&
                        oldDocId.split("_")[1].length === 2
                      ) {
                        oldDocId = oldDocId.replace(/_0+([1-9]\d*)_/g, "_$1_");
                      }
                      // Generate more possible ID variations for better matching
                      const possibleIds = new Set([
                        docId,
                        oldDocId,
                        docId.replace(/_0+(\d+)_/g, "_$1_"), // Remove leading zeros: UU_05_2023 -> UU_5_2023
                        docId.replace(/_(\d{1})_/g, "_0$1_"), // Add leading zeros: UU_5_2023 -> UU_05_2023
                        (node?.properties?.href as string).replace(
                          "https://chat.lexin.cs.ui.ac.id/details/",
                          ""
                        ), // Original URL-encoded version
                      ]);

                      let doc = null;

                      for (const document of (props?.chat?.documents as any) ||
                        []) {
                        const documentId = document._id || document.id;

                        // Check against all possible ID variations
                        for (const possibleId of possibleIds) {
                          if (
                            documentId === possibleId &&
                            !!document?.source &&
                            !document?.pasal
                          ) {
                            doc = document;
                            break;
                          }
                        }

                        if (doc) break; // Exit outer loop if found
                      }

                      if (
                        !references.has(docId) &&
                        doc &&
                        doc.source &&
                        !references.has(oldDocId)
                      ) {
                        const newReferences = new Map(references);
                        newReferences.set(docId, {
                          number: newReferences.size + 1,
                          href: node?.properties?.href as string,
                          doc,
                        });
                        setReferences(newReferences);
                      }

                      // Memoized fetch: only fetch if not already fetched
                      if (
                        !doc &&
                        !fetchedIds.current.has(docId) &&
                        !fetchedIds.current.has(oldDocId) &&
                        !references.has(docId) &&
                        !references.has(oldDocId)
                      ) {
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
                                  Jenis: "Kitab Undang-Undang",
                                },
                              },
                            },
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
                                  Judul: (children as string) || docId,
                                  "Bentuk Singkat": docId,
                                },
                              },
                            },
                          });
                          setReferences(newReferences);
                          // Continue to Dialog rendering below, don't return early
                        } else {
                          fetch(
                            `https://chat.lexin.cs.ui.ac.id/elasticsearch/peraturan_indonesia/_search`,
                            {
                              method: "POST",
                              headers: {
                                "Content-Type": "application/json",
                                Authorization: `Basic ${btoa(
                                  `elastic:password`
                                )}`,
                              },
                              body: JSON.stringify({
                                query: {
                                  bool: {
                                    should: Array.from(possibleIds).map(
                                      (id) => ({
                                        match: { _id: id },
                                      })
                                    ),
                                  },
                                },
                              }),
                            }
                          )
                            .then(async (res) => {
                              if (!res.ok) return;

                              const data = await res.json();
                              if (
                                data.hits &&
                                data.hits.hits &&
                                data.hits.hits.length > 0
                              ) {
                                const d = data.hits.hits[0];
                                doc = {
                                  _id: d._id,
                                  id: d._id,
                                  source: d._source,
                                  pasal: d._source.pasal || null,
                                };
                                if (doc && doc.source) {
                                  if (!props?.chat?.documents) {
                                    props.chat.documents = [] as any;
                                  }
                                  (props?.chat?.documents as any)?.push(doc);
                                  const newReferences = new Map(references);
                                  newReferences.set(docId, {
                                    number: newReferences.size + 1,
                                    href: node?.properties?.href as string,
                                    doc,
                                  });
                                  setReferences(newReferences);
                                }
                              }
                            })
                            .catch((error) => {
                              console.warn(
                                `Failed to fetch document ${docId}:`,
                                error.message
                              );
                            });
                        }
                      }

                      // If we have minimal reference data, create a minimal doc object to proceed
                      if (!doc || !doc.source) {
                        const refDoc =
                          references.get(docId) || references.get(oldDocId);
                        if (refDoc?.doc) {
                          doc = refDoc.doc;
                        } else {
                          // Create minimal doc structure for rendering
                          doc = {
                            _id: docId,
                            source: {
                              metadata: {
                                Judul: (childText as string) || docId,
                                "Bentuk Singkat": docId,
                              },
                            },
                          };
                        }
                      }

                      // For documents without metadata, try to create minimal reference info
                      const refDoc =
                        references.get(docId) || references.get(oldDocId);
                      if (!refDoc?.doc?.source?.metadata) {
                        // Create minimal reference for documents like KUH_Perdata
                        const newReferences = new Map(references);
                        newReferences.set(docId, {
                          number: newReferences.size + 1,
                          href: node?.properties?.href as string,
                          doc: {
                            ...doc,
                            source: {
                              ...doc.source,
                              metadata: {
                                ...doc.source.metadata,
                                Judul: doc.source.metadata?.Judul || docId,
                                "Bentuk Singkat":
                                  doc.source.metadata?.["Bentuk Singkat"] ||
                                  docId,
                              },
                            },
                          },
                        });
                        setReferences(newReferences);
                      }

                      // Render as superscript for numbered citations, regular button for others
                      return (
                        <DocumentDialog
                          docId={docId}
                          oldDocId={oldDocId}
                          references={references}
                          getPdfUrl={getPdfUrl}
                          isSuperscript={isCitation}
                          citationNumber={
                            isCitation ? (childText as string) : undefined
                          }
                        />
                      );
                    },
                  }}
                >
                  {cleanedText
                    .replace("```", "")
                    .replace(/\]\(([^)]+)\)/g, (_: string, url: string) => {
                      // Replace spaces with %20 in URLs
                      const encodedUrl = url.replace(/ /g, "%20");
                      return `](${encodedUrl})`;
                    })}
                </Markdown>

                {/* Reference List with Clickable Citations */}
                {props.sender === "assistant" &&
                  sortedReferences.length > 0 && (
                    <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                      <h4 className="font-semibold text-sm flex items-center gap-2 mb-3 text-[#192f59]">
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          width="16"
                          height="16"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          className="lucide lucide-book-marked"
                        >
                          <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                          <polyline points="10 2 10 10 13 7 16 10 16 2"></polyline>
                        </svg>
                        Referensi
                      </h4>
                      <div className="space-y-1.5 mb-5">
                        {sortedReferences.map((ref, index) => {
                          const docId = ref.doc?._id || ref.doc?.id;
                          const oldDocId = docId;
                          const metadata = ref.doc?.source?.metadata;
                          const bentukSingkat =
                            metadata?.["Bentuk Singkat"] ||
                            metadata?.Jenis ||
                            "";
                          const nomor = metadata?.Nomor
                            ? `No. ${metadata.Nomor}`
                            : "";
                          const tahun = metadata?.Tahun
                            ? `Tahun ${metadata.Tahun}`
                            : "";
                          const judul = metadata?.Judul || "Dokumen Hukum";

                          return (
                            <div
                              key={index}
                              className="flex items-start gap-2 text-sm hover:bg-gray-50 rounded px-2 py-1 transition-colors"
                            >
                              <span className="text-blue-600 font-bold text-xs mt-0.5 flex-shrink-0">
                                <DocumentDialog
                                  docId={docId}
                                  oldDocId={oldDocId}
                                  references={references}
                                  getPdfUrl={getPdfUrl}
                                  isSuperscript={false}
                                  citationNumber={`[${ref.number}]`}
                                />
                              </span>
                              <span className="text-gray-700 text-xs leading-relaxed">
                                <span className="font-medium">
                                  {[bentukSingkat, nomor, tahun]
                                    .filter(Boolean)
                                    .join(" ")}
                                </span>
                                {[bentukSingkat, nomor, tahun].filter(Boolean)
                                  .length > 0 && " - "}
                                {judul}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                <ActionBar
                  chat={props.chat}
                  messageId={props.messageId}
                  sessionId={props.sessionId}
                  text={text}
                  history={props.history}
                  finalThinkingDuration={props.finalThinkingDuration}
                />
              </div>
            </div>
          )}
        </div>
        {props.sender === "user" && (
          <UserCircle2 className="text-sm font-light mt-2 text-gray-600" />
        )}
      </div>
    </div>
  );
}
