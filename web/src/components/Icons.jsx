import React from 'react';

const shapes={
 chat:<><path d="M20 11a8 8 0 0 1-8 8H5l-3 3V11a9 9 0 0 1 18 0ZM7 10h8M7 14h5"/></>,
 chart:<><rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 9h16M4 15h16M9 4v16M15 4v16"/></>,
 library:<><path d="M4 5h5a4 4 0 0 1 3 1.5A4 4 0 0 1 15 5h5v14h-5a4 4 0 0 0-3 1.5A4 4 0 0 0 9 19H4zM12 7v13M7 9h2M7 12h2M15 9h2M15 12h2"/></>,
 compare:<><circle cx="9" cy="12" r="6"/><circle cx="15" cy="12" r="6"/><path d="M12 7v10"/></>,
 tools:<><circle cx="12" cy="12" r="8"/><path d="m15 9-2 4-4 2 2-4zM12 2v2M22 12h-2M12 22v-2M2 12h2"/></>,
 records:<><rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v18M12 8h4M12 12h4M12 16h3"/></>,
 sun:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5 19 19M19 5l-1.5 1.5M6.5 17.5 5 19"/></>,
 moon:<path d="M20 14.2A8.5 8.5 0 0 1 9.8 4 8.5 8.5 0 1 0 20 14.2Z"/>,
 star:<path d="m12 3 2.2 6.8L21 12l-6.8 2.2L12 21l-2.2-6.8L3 12l6.8-2.2Z"/>,
 arrow:<path d="M5 12h14m-5-5 5 5-5 5"/>,
 download:<><path d="M12 3v12m-4-4 4 4 4-4M5 16v4h14v-4"/></>,
 save:<><path d="M6 3h12v18l-6-4-6 4z"/></>,
 pin:<><path d="M18 10c0 5-6 11-6 11S6 15 6 10a6 6 0 1 1 12 0Z"/><circle cx="12" cy="10" r="2"/></>,
 pause:<><path d="M8 5v14M16 5v14"/></>,
 play:<path d="m9 5 10 7-10 7Z"/>,
 source:<><path d="M14 4h6v6M20 4l-9 9M11 5H5v14h14v-6"/></>,
 sparkle:<><path d="m12 3 2.2 6.8L21 12l-6.8 2.2L12 21l-2.2-6.8L3 12l6.8-2.2Z"/><path d="M20 2v4M18 4h4"/></>,
 search:<><circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/></>,
 clock:<><circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 2"/></>,
 check:<path d="m5 12 4 4L19 6"/>,
};

export function Icon({name='star',size=20,className=''}){
 return <svg className={'icon '+className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{shapes[name]||shapes.star}</svg>;
}

export function StarMark({className=''}){
 return <svg className={'star-mark '+className} viewBox="0 0 64 64" fill="none" aria-hidden="true"><circle cx="32" cy="32" r="27" stroke="currentColor" strokeWidth=".7"/><circle cx="32" cy="32" r="21" stroke="currentColor" strokeWidth=".6" strokeDasharray="1 5"/><path d="m32 10 4.8 17.2L54 32l-17.2 4.8L32 54l-4.8-17.2L10 32l17.2-4.8Z" stroke="currentColor" strokeWidth="1.2"/><circle cx="32" cy="32" r="4" fill="currentColor"/><path d="m17 16 30 32M47 16 17 48" stroke="currentColor" strokeWidth=".6"/></svg>;
}
