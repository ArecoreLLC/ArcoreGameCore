import {useEffect,useRef} from 'react';

export default function AboutDialog({version,onClose}:{version:string;onClose:()=>void}){
 const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{const el=dialog.current;const previous=document.activeElement as HTMLElement|null;el?.showModal();return()=>{el?.close();previous?.focus()}},[]);
 return <dialog ref={dialog} className="modal compact about-dialog" aria-labelledby="about-title" onCancel={onClose}>
  <img className="arcore-mark" src="/arcore-mark.svg" alt=""/>
  <h2 id="about-title">Arcore GameCore</h2>
  <p>Arecore LLC · Version {version}</p>
  <p>Your studio library for games, reusable modules, media and production workflows.</p>
  <p className="small">Choose a workspace section to browse your library. Open a project to review its details and media. Use Back up library to export a copy of your local library.</p>
  <div className="modal-actions"><button autoFocus onClick={onClose}>Close</button></div>
 </dialog>;
}
