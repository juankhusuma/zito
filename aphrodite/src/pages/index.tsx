import { Flag, Search, ArrowRight, Shield, BookOpen, ChevronDown } from "lucide-react"
import PrimaryButton from "../components/button"
import { useEffect, useState } from "react"

export default function Home() {
    const [scrollY, setScrollY] = useState(0);
    const [isVisible, setIsVisible] = useState(false);

    // Handle scroll events for parallax and reveal animations
    useEffect(() => {
        const handleScroll = () => {
            setScrollY(window.scrollY);
        };

        // Set initial visibility after a slight delay for entrance animation
        const timer = setTimeout(() => {
            setIsVisible(true);
        }, 300);

        window.addEventListener("scroll", handleScroll);
        return () => {
            window.removeEventListener("scroll", handleScroll);
            clearTimeout(timer);
        };
    }, []);

    // Floating animation for CTA buttons
    const floatingAnimation = "animate-float";

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-b from-white to-gray-50">
            {/* Hero Section with Parallax Effect */}
            <div className='relative w-full h-[500px] lg:h-[600px] z-0 flex items-center justify-center overflow-hidden'>
                <div className='absolute z-[100] bg-gradient-to-r from-[#192f59]/90 to-[#192f59]/80 top-0 left-0 w-full h-full'></div>
                <img
                    className='absolute z-0 w-full h-full object-cover object-center scale-105 filter brightness-75'
                    src="/hukum.jpg"
                    alt='law'
                    style={{ transform: `translateY(${scrollY * 0.2}px)` }} // Parallax effect
                />

                <div className='relative z-[200] container mx-auto px-6 lg:px-8 h-full flex flex-col items-center justify-center'>
                    <div className="text-center max-w-3xl mx-auto">
                        <div className={`transition-all duration-1000 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                            <h1 className='font-bold text-4xl lg:text-6xl mb-6 text-white leading-tight drop-shadow-md'>
                                Legal <span className="bg-clip-text text-transparent bg-gradient-to-r from-blue-200 to-cyan-100 animate-gradient-x">Generative-AI</span><br />
                                <span className="text-blue-200 inline-block">Search</span>
                            </h1>
                            <p className='text-gray-100 text-lg lg:text-xl mb-10 max-w-2xl mx-auto leading-relaxed'>
                                Buka wawasan hukum yang tak tertandingi dengan basis data hukum berbasis AI, merevolusi pengalaman riset hukum Anda.
                            </p>
                        </div>

                        <div className={`flex flex-col sm:flex-row gap-4 justify-center transition-all duration-1000 delay-300 transform ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
                            <a href="/chat" className={`w-full sm:w-auto ${floatingAnimation}`}>
                                <PrimaryButton
                                    type='button'
                                    className='py-3 px-8 text-lg bg-white text-[#192f59] hover:bg-blue-50 shadow-lg hover:shadow-xl justify-center gap-2 w-full sm:w-auto transition-all duration-300 rounded-xl hover:scale-105'
                                >
                                    <span className="font-semibold text-[#192f59] text-center w-full">Coba Sekarang</span>
                                    <ArrowRight size={18} className="text-[#192f59] animate-bounce-horizontal" />
                                </PrimaryButton>
                            </a>
                            <a href="#features" className="w-full sm:w-auto group">
                                <button className="py-3 px-8 text-lg bg-transparent border border-white/30 text-white hover:bg-white/10 hover:border-white shadow-lg hover:shadow-xl flex items-center justify-center gap-2 w-full sm:w-auto transition-all duration-300 rounded-xl hover:scale-105">
                                    <span className="font-medium">Pelajari Lebih Lanjut</span>
                                    <ChevronDown size={18} className="transition-transform duration-300 group-hover:translate-y-1" />
                                </button>
                            </a>
                        </div>
                    </div>
                </div>

                {/* Animated Wave Divider */}
                <div className="absolute bottom-0 left-0 w-full opacity-40">
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 220" className="animate-wave">
                        <path fill="#ffffff" fillOpacity="1" d="M0,160L48,144C96,128,192,96,288,90.7C384,85,480,107,576,122.7C672,139,768,149,864,138.7C960,128,1056,96,1152,85.3C1248,75,1344,85,1392,90.7L1440,96L1440,320L1392,320C1344,320,1248,320,1152,320C1056,320,960,320,864,320C768,320,672,320,576,320C480,320,384,320,288,320C192,320,96,320,48,320L0,320Z"></path>
                    </svg>
                </div>
            </div>

            {/* Features Section with Scroll Reveal */}
            <div id="features" className="w-full py-20 px-6 lg:px-8">
                <div className="container mx-auto">
                    <div className='mb-16 text-center reveal-element'>
                        <div className="inline-block px-3 py-1 rounded-full bg-blue-100 text-[#192f59] font-semibold text-sm mb-3 animate-pulse">
                            FITUR UNGGULAN
                        </div>
                        <h2 className='text-3xl lg:text-4xl font-bold text-[#192f59] mb-4'>
                            Asisten Hukum Pintar Anda
                        </h2>
                        <div className='h-1 w-24 bg-gradient-to-r from-[#d61b23] to-[#ff6b6b] mx-auto mb-6 rounded-full animate-expand'></div>
                        <p className='text-gray-600 max-w-2xl mx-auto text-lg'>
                            Akses database hukum Indonesia dengan mudah melalui kecerdasan buatan yang responsif dan akurat.
                        </p>
                    </div>

                    <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16'>
                        {/* Feature Card 1 - with hover and reveal animations */}
                        <div className='bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 border border-gray-100 feature-card hover:border-blue-200 feature-reveal-1'>
                            <div className='bg-blue-100 p-4 rounded-2xl w-16 h-16 flex items-center justify-center mb-6 mx-auto transform transition-transform hover:rotate-12 hover:scale-110 hover:bg-blue-200'>
                                <Search size={28} className="text-[#192f59]" />
                            </div>
                            <h3 className='text-xl font-bold text-[#192f59] mb-4 text-center'>Jawaban Kontekstual</h3>
                            <p className='text-gray-600 mb-6'>Menjawab pertanyaan hukum dengan memahami konteks pertanyaan dalam bahasa alami, tanpa terbatas pada pencarian kata kunci.</p>
                            <ul className='space-y-3'>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Memahami bahasa alami</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Respons berbasis dokumen hukum Indonesia</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Relevan untuk berbagai jenis pertanyaan</p>
                                </li>
                            </ul>
                        </div>

                        {/* Feature Card 2 */}
                        <div className='bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 border border-gray-100 feature-card hover:border-blue-200 feature-reveal-2'>
                            <div className='bg-blue-100 p-4 rounded-2xl w-16 h-16 flex items-center justify-center mb-6 mx-auto transform transition-transform hover:rotate-12 hover:scale-110 hover:bg-blue-200'>
                                <BookOpen size={28} className="text-[#192f59]" />
                            </div>
                            <h3 className='text-xl font-bold text-[#192f59] mb-4 text-center'>Akses ke Dokumen Hukum</h3>
                            <p className='text-gray-600 mb-6'>Menggunakan sumber terbuka seperti Undang-Undang dan peraturan sebagai basis data dengan referensi yang akurat.</p>
                            <ul className='space-y-3'>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Menggunakan sumber hukum publik</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Fokus pada sumber hukum primer</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Diupdate secara berkala</p>
                                </li>
                            </ul>
                        </div>

                        {/* Feature Card 3 */}
                        <div className='bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 p-8 border border-gray-100 feature-card hover:border-blue-200 feature-reveal-3'>
                            <div className='bg-blue-100 p-4 rounded-2xl w-16 h-16 flex items-center justify-center mb-6 mx-auto transform transition-transform hover:rotate-12 hover:scale-110 hover:bg-blue-200'>
                                <Shield size={28} className="text-[#192f59]" />
                            </div>
                            <h3 className='text-xl font-bold text-[#192f59] mb-4 text-center'>Rujukan Tersurat</h3>
                            <p className='text-gray-600 mb-6'>Setiap jawaban disertai kutipan atau petunjuk sumber hukum yang relevan untuk verifikasi dan penelusuran.</p>
                            <ul className='space-y-3'>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Kutipan langsung dari dokumen hukum</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Mencantumkan nomor pasal</p>
                                </li>
                                <li className='flex items-start gap-3 feature-list-item'>
                                    <div className="bg-[#d61b23] rounded-full p-1 mt-1 animate-ping-small">
                                        <Flag className="w-3 h-3 text-white" />
                                    </div>
                                    <p className='text-gray-700'>Memudahkan verifikasi manual</p>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>

            {/* CTA Section with Gradient Animation */}
            <div className="w-full py-16 bg-gradient-to-r from-[#192f59] to-[#1e3a6b] animate-gradient-slow relative overflow-hidden">
                {/* Animated subtle background particles */}
                <div className="absolute inset-0 overflow-hidden">
                    <div className="particle"></div>
                    <div className="particle"></div>
                    <div className="particle"></div>
                </div>

                <div className="container mx-auto px-6 lg:px-8 text-center relative z-10">
                    <h2 className="text-3xl lg:text-4xl font-bold text-white mb-6 animate-fadeIn">Siap untuk memulai?</h2>
                    <p className="text-blue-100 mb-10 max-w-2xl mx-auto animate-fadeIn">Akses database hukum terlengkap dengan teknologi AI terbaru untuk pengalaman riset hukum yang lebih baik.</p>
                    <a href="/chat" className={floatingAnimation}>
                        <PrimaryButton
                            type='button'
                            className='py-3 px-8 text-lg bg-white text-[#192f59] hover:bg-blue-50 shadow-lg inline-flex items-center justify-center gap-2 transition-all duration-300 rounded-xl hover:scale-110'
                        >
                            <span className="font-semibold text-[#192f59] text-center w-full">Mulai Sekarang</span>
                            <ArrowRight size={18} className="text-[#192f59] animate-bounce-horizontal" />
                        </PrimaryButton>
                    </a>
                </div>
            </div>

            {/* Footer */}
            <footer className="w-full py-8 bg-gray-50 border-t border-gray-200">
                <div className="container mx-auto px-6 lg:px-8 text-center text-gray-500 text-sm">
                    © {new Date().getFullYear()} Lexin AI. Semua hak dilindungi.
                </div>
            </footer>
        </div>
    );
}