'use client';

import { useEffect, useRef, useState } from 'react';
import {
  ColorType, CrosshairMode, createChart,
  type IChartApi, type ISeriesApi, type SeriesMarker, type Time,
} from 'lightweight-charts';

// ─── Public Types ─────────────────────────────────────────────────────────────
export type WatchlistAsset = 'BTCUSD' | 'ETHUSD' | 'XAUUSD' | 'LTCUSD';
export type Timeframe      = '5m' | '15m' | '30m' | '1h' | '2h' | '4h' | '1d';
/** 'bitstamp' = Bitstamp (crypto) + FOREXCOM (XAU)  |  'binance' = Binance (crypto) + OANDA (XAU) */
export type DataSourceType = 'bitstamp' | 'binance';

export interface AISignal {
  asset: WatchlistAsset; timestamp: number; price: number;
  action: 'BUY' | 'SELL' | 'HOLD' | 'STOP LOSS' | 'STOP_LOSS';
  message: string; color: string;
}

export interface ChartComponentProps {
  asset: WatchlistAsset;
  aiSignals: AISignal[];
  subscriptionActive: boolean;
  wsBaseUrl: string;
  timeframe: Timeframe;
  onTimeframeChange: (tf: Timeframe) => void;
  showFullDashboardButton?: boolean;
  onPriceUpdate?: (asset: WatchlistAsset, price: number) => void;
  dataSource?: DataSourceType;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const TIMEFRAMES: Timeframe[] = ['5m','15m','30m','1h','2h','4h','1d'];

const TF_SEC: Record<Timeframe,number> = {
  '5m':300,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,
};
const TF_LIMIT: Record<Timeframe,number> = {
  '5m':1000,'15m':1000,'30m':1000,'1h':750,'2h':375,'4h':200,'1d':180,
};

// Bitstamp
const BS_PAIR: Record<WatchlistAsset,string|null> = {
  BTCUSD:'btcusd', ETHUSD:'ethusd', LTCUSD:'ltcusd', XAUUSD:null,
};
const BS_STEP: Record<Timeframe,number> = {
  '5m':300,'15m':900,'30m':1800,'1h':3600,'2h':7200,'4h':14400,'1d':86400,
};

// Binance
const BN_SYM: Record<WatchlistAsset,string> = {
  BTCUSD:'BTCUSDT', ETHUSD:'ETHUSDT', XAUUSD:'PAXGUSDT', LTCUSD:'LTCUSDT',
};
const BN_WS: Record<WatchlistAsset,string> = {
  BTCUSD:'btcusdt', ETHUSD:'ethusdt', XAUUSD:'paxgusdt', LTCUSD:'ltcusdt',
};
const BN_TF: Record<Timeframe,string> = {
  '5m':'5m','15m':'15m','30m':'30m','1h':'1h','2h':'2h','4h':'4h','1d':'1d',
};

const COLOR_UP   = '#26a69a';
const COLOR_DOWN = '#ef5350';
const SIXTY_MIN  = 3600;

// ─── Types ────────────────────────────────────────────────────────────────────
interface Candle { time:Time; open:number; high:number; low:number; close:number; }
interface SignalPayload {
  type:'signal'; asset:string; timeframe:string; signal:'BUY'|'SELL';
  is_bullish:boolean; price:number; timestamp:string; bar_index:number; tracking:string;
  all_zones:Array<{is_bullish:boolean; center_price:number; timestamp:string; bar_index:number}>;
}
interface BinanceKlineMsg { e:string; k:{t:number;o:string;h:string;l:string;c:string;x:boolean}; }

// ─── Helpers ──────────────────────────────────────────────────────────────────
const toF = (v:string|number|null|undefined, fb=0):number => {
  const n = typeof v==='string' ? parseFloat(v) : (v??NaN);
  return Number.isFinite(n) && (n as number)>0 ? (n as number) : fb;
};
const bkoff = (n:number) => Math.min(1000*Math.pow(2,Math.min(n-1,3)),10_000);

function srcLabel(asset:WatchlistAsset, ds:DataSourceType):string {
  if (asset==='XAUUSD') return ds==='bitstamp' ? 'FOREXCOM' : 'OANDA';
  return ds==='bitstamp' ? 'BITSTAMP' : 'BINANCE';
}

// ─── Component ───────────────────────────────────────────────────────────────
export default function ChartComponent({
  asset, subscriptionActive, wsBaseUrl,
  timeframe, onTimeframeChange,
  showFullDashboardButton=false, onPriceUpdate,
  dataSource='bitstamp',
}: ChartComponentProps) {

  const containerRef  = useRef<HTMLDivElement|null>(null);
  const chartRef      = useRef<IChartApi|null>(null);
  const seriesRef     = useRef<ISeriesApi<'Candlestick'>|null>(null);
  const roRef         = useRef<ResizeObserver|null>(null);
  const markersRef    = useRef<Map<number,SeriesMarker<Time>>>(new Map());
  const chartStartRef = useRef<number>(0);

  const [lastPrice,    setLastPrice]    = useState<number|null>(null);
  const [connected,    setConnected]    = useState<boolean|null>(null);
  const [signalStatus, setSignalStatus] = useState<{last_signal:string;tracking:string}|null>(null);
  const [sigLoading,   setSigLoading]   = useState(false);

  const userTZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

  // ── Create chart once ─────────────────────────────────────────────────────
  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      autoSize:true,
      layout:{ background:{type:ColorType.Solid,color:'#020617'}, textColor:'#cbd5e1' },
      grid:{ vertLines:{color:'rgba(148,163,184,0.07)'}, horzLines:{color:'rgba(148,163,184,0.07)'} },
      crosshair:{ mode:CrosshairMode.Normal,
        vertLine:{color:'#758BFD',width:1,style:2}, horzLine:{color:'#758BFD',width:1,style:2} },
      rightPriceScale:{ borderColor:'rgba(148,163,184,0.2)', textColor:'#cbd5e1',
        scaleMargins:{top:0.10,bottom:0.08} },
      localization:{ timeFormatter:(sec:number) =>
        new Intl.DateTimeFormat(undefined,{
          year:'2-digit',month:'2-digit',day:'2-digit',
          hour:'2-digit',minute:'2-digit',hour12:false,timeZone:userTZ,
        }).format(new Date(sec*1000)).replace(',','') },
      timeScale:{ borderColor:'rgba(148,163,184,0.2)', timeVisible:true, secondsVisible:false,
        fixLeftEdge:true, fixRightEdge:true, lockVisibleTimeRangeOnResize:true },
      handleScroll:{mouseWheel:true,pressedMouseMove:true,horzTouchDrag:true,vertTouchDrag:true},
      handleScale:{axisPressedMouseMove:true,mouseWheel:true,pinch:true},
      kineticScroll:{mouse:false,touch:true}, watermark:{visible:false},
    });
    const series = chart.addCandlestickSeries({
      upColor:COLOR_UP, downColor:COLOR_DOWN,
      wickUpColor:COLOR_UP, wickDownColor:COLOR_DOWN,
      borderVisible:true, borderUpColor:COLOR_UP, borderDownColor:COLOR_DOWN,
      priceLineVisible:true, priceLineColor:COLOR_UP, priceLineWidth:1,
      priceFormat:{type:'price',precision:2,minMove:0.01},
    });
    chartRef.current=chart; seriesRef.current=series;
    roRef.current=new ResizeObserver(()=>{
      if(containerRef.current&&chartRef.current)
        chartRef.current.applyOptions({
          width:containerRef.current.clientWidth,
          height:containerRef.current.clientHeight,
        });
    });
    roRef.current.observe(containerRef.current);
    return ()=>{roRef.current?.disconnect();chart.remove();chartRef.current=null;seriesRef.current=null;};
  },[]);

  // ── Data + connections per asset/timeframe/source ─────────────────────────
  useEffect(()=>{
    setLastPrice(null); setSignalStatus(null); setSigLoading(true);
    chartStartRef.current=0; markersRef.current.clear();
    seriesRef.current?.setData([]); seriesRef.current?.setMarkers([]);

    const candles   = new Map<number,Candle>();
    const tickBuf:  Array<()=>void> = [];
    let histLoaded  = false;
    const gone      = {current:false};

    // ── Markers ───────────────────────────────────────────────────────────────
    const flushMarkers = (minTime=chartStartRef.current) => {
      if (!seriesRef.current) return;
      const all = [...markersRef.current.values()];
      const vis = minTime>0 ? all.filter(m=>(m.time as number)>=minTime) : all;
      try { seriesRef.current.setMarkers(vis.sort((a,b)=>(a.time as number)-(b.time as number))); }
      catch { /* resetting */ }
    };

    const zoneToMarker = (z:{is_bullish:boolean;timestamp:string}, ivl:number):SeriesMarker<Time> => {
      const ts  = z.timestamp.endsWith('Z')||z.timestamp.includes('+') ? z.timestamp : z.timestamp+'Z';
      const raw = Math.floor(new Date(ts).getTime()/1000);
      return {
        time:  Math.floor(raw/ivl)*ivl as Time,
        position: z.is_bullish?'belowBar':'aboveBar',
        color:    z.is_bullish?COLOR_UP:COLOR_DOWN,
        shape:    z.is_bullish?'arrowUp':'arrowDown',
        text:     z.is_bullish?'BUY SIGNAL':'SELL SIGNAL',
        size:2,
      };
    };

    const mergeAndFlush = (incoming:SeriesMarker<Time>[]) => {
      const sorted=[...incoming].sort((a,b)=>(a.time as number)-(b.time as number));
      for (const m of sorted) {
        const t=m.time as number;
        if (markersRef.current.has(t)) continue;
        const keys=[...markersRef.current.keys()].sort((a,b)=>a-b);
        const lt=keys.length?keys[keys.length-1]:undefined;
        const last=lt!==undefined?markersRef.current.get(lt):undefined;
        if (last&&lt!==undefined) {
          if (t-lt<SIXTY_MIN) {
            if (last.text===m.text&&t>lt){markersRef.current.delete(lt);markersRef.current.set(t,m);}
            continue;
          }
          if (last.text===m.text){if(t>lt){markersRef.current.delete(lt);markersRef.current.set(t,m);}continue;}
        }
        if(!chartStartRef.current||t>=chartStartRef.current) markersRef.current.set(t,m);
      }
      flushMarkers();
    };

    const applySignal=(s:SignalPayload)=>{
      const ivl=TF_SEC[timeframe];
      const markers=s.all_zones.map(z=>zoneToMarker(z,ivl));
      const vis=chartStartRef.current?markers.filter(m=>(m.time as number)>=chartStartRef.current):markers;
      if(vis.length){mergeAndFlush(vis);setSignalStatus({last_signal:s.signal,tracking:s.tracking});}
    };

    // ── Unified price tick ────────────────────────────────────────────────────
    const applyTick=(open:number,high:number,low:number,close:number,tsMs:number)=>{
      const ivl=TF_SEC[timeframe];
      const start=Math.floor(tsMs/1000/ivl)*ivl;
      const ex=candles.get(start);
      const c:Candle=ex
        ?{time:start as Time,open:ex.open,high:Math.max(ex.high,high),low:Math.min(ex.low,low),close}
        :{time:start as Time,open,high,low,close};
      candles.set(start,c);
      setLastPrice(close); onPriceUpdate?.(asset,close);
      try{seriesRef.current?.update(c);}catch{/*ignore*/}
    };

    // ─────────────────────────────────────────────────────────────────────────
    // BACKEND WebSocket — signals only (BUY/SELL markers)
    // ─────────────────────────────────────────────────────────────────────────
    let backendWs:WebSocket|null=null;
    let bkRetries=0;
    let bkTimer:ReturnType<typeof setTimeout>|null=null;
    let bkHB:ReturnType<typeof setInterval>|null=null;
    let bkStale:ReturnType<typeof setTimeout>|null=null;

    const resetStale=()=>{
      if(bkStale)clearTimeout(bkStale);
      bkStale=setTimeout(()=>{
        if(!gone.current&&backendWs?.readyState===WebSocket.OPEN) backendWs.close(4000,'stale');
      },45_000);
    };
    const connectBackend=()=>{
      if(gone.current)return;
      try{backendWs=new WebSocket(`${wsBaseUrl}/ws/market/${asset}/${timeframe}/`);}
      catch{schedBkRetry();return;}
      backendWs.onopen=()=>{bkRetries=0;resetStale();
        bkHB=setInterval(()=>{if(backendWs?.readyState===WebSocket.OPEN)
          try{backendWs!.send(JSON.stringify({action:'ping'}));}catch{/**/}},20_000);};
      backendWs.onmessage=(ev:MessageEvent<string>)=>{
        resetStale();
        try{
          const raw=JSON.parse(ev.data) as Record<string,unknown>;
          if(raw.type==='ping'){backendWs?.send(JSON.stringify({action:'pong'}));return;}
          if(raw.type==='signal'&&histLoaded) applySignal(raw as unknown as SignalPayload);
        }catch{/**/}
      };
      backendWs.onclose=()=>{
        if(bkHB){clearInterval(bkHB);bkHB=null;}
        if(bkStale){clearTimeout(bkStale);bkStale=null;}
        schedBkRetry();
      };
      backendWs.onerror=()=>{/*onclose fires*/};
    };
    const schedBkRetry=()=>{if(gone.current)return;bkRetries++;bkTimer=setTimeout(connectBackend,Math.min(1000*Math.pow(2,Math.min(bkRetries-1,4)),15_000));};

    // ─────────────────────────────────────────────────────────────────────────
    // SOURCE A — BITSTAMP (default for BTC/ETH/LTC) + FOREXCOM via proxy (XAU)
    // ─────────────────────────────────────────────────────────────────────────
    let bsWs:WebSocket|null=null;
    let bsRetries=0;
    let bsTimer:ReturnType<typeof setTimeout>|null=null;
    let xauInterval:ReturnType<typeof setInterval>|null=null;

    const loadBitstampHistory=async():Promise<Candle[]>=>{
      const pair=BS_PAIR[asset]!;
      const step=BS_STEP[timeframe];
      const limit=TF_LIMIT[timeframe];
      const end=Math.floor(Date.now()/1000)+step;
      const r=await fetch(`https://www.bitstamp.net/api/v2/ohlc/${pair}/?step=${step}&limit=${limit}&end=${end}`);
      const j=await r.json();
      return (j.data?.ohlc??[]).map((c:Record<string,string>)=>({
        time:parseInt(c.timestamp) as Time,
        open:toF(c.open),high:toF(c.high),low:toF(c.low),close:toF(c.close),
      }));
    };

    const connectBitstamp=()=>{
      if(gone.current)return;
      const pair=BS_PAIR[asset];
      if(!pair)return;
      try{bsWs=new WebSocket('wss://ws.bitstamp.net');}
      catch{schedBsRetry();return;}
      bsWs.onopen=()=>{
        setConnected(true);bsRetries=0;
        bsWs!.send(JSON.stringify({event:'bts:subscribe',data:{channel:`live_trades_${pair}`}}));
      };
      bsWs.onmessage=(ev:MessageEvent<string>)=>{
        try{
          const msg=JSON.parse(ev.data) as Record<string,unknown>;
          if(msg.event!=='trade')return;
          const d=msg.data as Record<string,unknown>;
          const price=toF(d.price as string|number);
          const tsMs=parseInt(d.timestamp as string)*1000;
          if(!price)return;
          const apply=()=>applyTick(price,price,price,price,tsMs);
          if(!histLoaded)tickBuf.push(apply);else apply();
        }catch{/**/}
      };
      bsWs.onclose=()=>{setConnected(false);schedBsRetry();};
      bsWs.onerror=()=>{setConnected(false);};
    };
    const schedBsRetry=()=>{if(gone.current)return;bsRetries++;bsTimer=setTimeout(connectBitstamp,bkoff(bsRetries));};

    const startXauPoll=(source:'forexcom'|'oanda')=>{
      const poll=async()=>{
        if(gone.current)return;
        try{
          const r=await fetch(`/api/market/xau-price/?source=${source}`);
          const d=await r.json();
          if(d.success&&d.price>0){
            const p=d.price as number;
            const apply=()=>applyTick(p,p,p,p,Date.now());
            if(!histLoaded)tickBuf.push(apply);else apply();
            if(!gone.current)setConnected(true);
          }
        }catch{/*non-fatal*/}
      };
      poll();
      xauInterval=setInterval(poll,10_000);
    };

    // ─────────────────────────────────────────────────────────────────────────
    // SOURCE B — BINANCE (option for BTC/ETH/LTC) + OANDA via proxy (XAU)
    // ─────────────────────────────────────────────────────────────────────────
    let bnWs:WebSocket|null=null;
    let bnRetries=0;
    let bnTimer:ReturnType<typeof setTimeout>|null=null;

    const loadBinanceHistory=async():Promise<Candle[]>=>{
      const sym=BN_SYM[asset];
      const r=await fetch(`https://api.binance.com/api/v3/klines?symbol=${sym}&interval=${BN_TF[timeframe]}&limit=${TF_LIMIT[timeframe]}`);
      const raw:(string|number)[][]=await r.json();
      return raw.map(k=>({
        time:Math.floor(Number(k[0])/1000) as Time,
        open:toF(k[1] as string),high:toF(k[2] as string),
        low:toF(k[3] as string),close:toF(k[4] as string),
      }));
    };

    const connectBinance=()=>{
      if(gone.current)return;
      try{bnWs=new WebSocket(`wss://stream.binance.com:9443/ws/${BN_WS[asset]}@kline_${BN_TF[timeframe]}`);}
      catch{schedBnRetry();return;}
      bnWs.onopen=()=>{setConnected(true);bnRetries=0;};
      bnWs.onmessage=(ev:MessageEvent<string>)=>{
        try{
          const msg=JSON.parse(ev.data) as BinanceKlineMsg;
          if(msg.e!=='kline')return;
          const k=msg.k;
          const apply=()=>applyTick(toF(k.o),toF(k.h),toF(k.l),toF(k.c),k.t);
          if(!histLoaded)tickBuf.push(apply);else apply();
        }catch{/**/}
      };
      bnWs.onclose=()=>{setConnected(false);schedBnRetry();};
      bnWs.onerror=()=>{setConnected(false);};
    };
    const schedBnRetry=()=>{if(gone.current)return;bnRetries++;bnTimer=setTimeout(connectBinance,bkoff(bnRetries));};

    // ── History loader ────────────────────────────────────────────────────────
    const loadHistory=async()=>{
      try{
        let hist:Candle[]=[];
        if(asset==='XAUUSD'){
          const src=dataSource==='bitstamp'?'forexcom':'oanda';
          const r=await fetch(`/api/market/xau-ohlc/?timeframe=${timeframe}&source=${src}`);
          const d=await r.json();
          if(d.success){
            hist=(d.candles as Array<Record<string,number>>).map(c=>({
              time:c.time as Time,open:c.open,high:c.high,low:c.low,close:c.close,
            }));
          }
        } else if(dataSource==='bitstamp'){
          hist=await loadBitstampHistory();
        } else {
          hist=await loadBinanceHistory();
        }
        if(gone.current)return;

        // Deduplicate and sort
        const seen=new Map<number,Candle>();
        for(const c of hist) seen.set(c.time as number,c);
        const sorted=[...seen.values()].sort((a,b)=>(a.time as number)-(b.time as number));

        for(const c of sorted) candles.set(c.time as number,c);
        seriesRef.current?.setData(sorted);
        chartRef.current?.timeScale().fitContent();

        if(sorted.length){
          const latest=sorted[sorted.length-1].close;
          setLastPrice(latest);
          onPriceUpdate?.(asset,latest);
          chartStartRef.current=sorted[0].time as number;
        }

        histLoaded=true;
        for(const fn of tickBuf) fn();
        tickBuf.length=0;

        await fetchSignals(chartStartRef.current);
      }catch(e){
        console.error('History load failed:',e);
        histLoaded=true;
        for(const fn of tickBuf)fn();
        tickBuf.length=0;
        if(!gone.current)setSigLoading(false);
      }
    };

    // ── REST historical signals ───────────────────────────────────────────────
    const fetchSignals=async(chartStart=0)=>{
      if(!seriesRef.current||gone.current)return;
      const ivl=TF_SEC[timeframe];
      markersRef.current.clear();
      try{
        const allRaw:Array<{is_bullish:boolean;timestamp:string}>=[];
        try{
          const r=await fetch(`/api/trading/signal-history/${asset}/?timeframe=${timeframe}`);
          if(r.ok&&!gone.current){const j=await r.json();if(j.success)allRaw.push(...(j.signals??[]));}
        }catch{/*optional*/}
        if(gone.current)return;

        let liveStatus:{last_signal:string;tracking:string}|null=null;
        try{
          const r=await fetch(`/api/trading/reversal-zones/${asset}/?timeframe=${timeframe}`);
          if(r.ok&&!gone.current){
            const j=await r.json();
            if(j.success&&j.data?.zones?.length){allRaw.push(...j.data.zones);liveStatus=j.data.status??null;}
          }
        }catch{/*optional*/}
        if(gone.current)return;

        const sorted=allRaw.map(z=>zoneToMarker(z,ivl)).sort((a,b)=>(a.time as number)-(b.time as number));
        const seen=new Set<number>();
        const finalArr:SeriesMarker<Time>[]=[];
        for(const m of sorted){
          const t=m.time as number;
          if(seen.has(t))continue;
          const last=finalArr.length?finalArr[finalArr.length-1]:undefined;
          const lt=last?(last.time as number):undefined;
          if(lt!==undefined){
            if(t-lt<SIXTY_MIN){
              if(last?.text===m.text&&t>lt){finalArr[finalArr.length-1]=m;seen.delete(lt);seen.add(t);}
              continue;
            }
            if(last?.text===m.text){finalArr[finalArr.length-1]=m;seen.delete(lt!);seen.add(t);continue;}
          }
          finalArr.push(m);seen.add(t);
        }
        const vis=chartStart?finalArr.filter(m=>(m.time as number)>=chartStart):finalArr;
        for(const m of vis)markersRef.current.set(m.time as number,m);
        flushMarkers(chartStart);
        if(!gone.current&&liveStatus)setSignalStatus(liveStatus);
      }catch{/*silent*/}
      finally{if(!gone.current)setSigLoading(false);}
    };

    // ── Boot ─────────────────────────────────────────────────────────────────
    connectBackend();

    if(asset==='XAUUSD'){
      setConnected(null);
      startXauPoll(dataSource==='bitstamp'?'forexcom':'oanda');
    } else if(dataSource==='bitstamp'){
      connectBitstamp();
    } else {
      connectBinance();
    }

    loadHistory();

    return()=>{
      gone.current=true;
      if(bsTimer)clearTimeout(bsTimer);
      if(bnTimer)clearTimeout(bnTimer);
      if(bkTimer)clearTimeout(bkTimer);
      if(bkHB)clearInterval(bkHB);
      if(bkStale)clearTimeout(bkStale);
      if(xauInterval)clearInterval(xauInterval);
      try{bsWs?.close();}catch{/**/}
      try{bnWs?.close();}catch{/**/}
      try{backendWs?.close();}catch{/**/}
    };
  },[asset,wsBaseUrl,timeframe,dataSource]);

  // ─── Render ───────────────────────────────────────────────────────────────
  const src=srcLabel(asset,dataSource);

  return (
    <section className="relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/70 shadow-2xl shadow-black/20">

      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 px-5 py-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">Live Chart</p>
          <h2 className="mt-1 text-xl font-semibold text-white">{asset}</h2>
          <p className="text-sm text-slate-400">Real-time candlestick chart with reversal signals.</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Chart Feed: </span>
            <span className={connected===null?'text-amber-400':connected?'text-emerald-400':'text-rose-400'}>
              {connected===null?'Connecting…':connected?'Live ●':'Reconnecting…'}
            </span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Price: </span>
            <span className="font-bold text-white">
              {lastPrice===null?'—':lastPrice.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}
            </span>
          </div>
          <div className="rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">Source: </span>
            <span className="font-semibold text-cyan-300">{src}</span>
          </div>
          <div className="rounded-xl border border-slate-800 bg-slate-950 px-3 py-2 text-sm">
            <span className="text-slate-400">TZ: </span>
            <span className="font-medium text-cyan-300">{userTZ.split('/').pop()?.replace(/_/g,' ')}</span>
          </div>
          {signalStatus&&timeframe!=='4h'&&(
            <div className="min-w-[170px] rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Signal:</span>
                <span className={`font-bold ${
                  signalStatus.last_signal==='BUY'?'text-[#26a69a]':
                  signalStatus.last_signal==='SELL'?'text-[#ef5350]':'text-slate-300'}`}>
                  {signalStatus.last_signal==='BUY'?'▲ BUY':signalStatus.last_signal==='SELL'?'▼ SELL':signalStatus.last_signal}
                </span>
              </div>
              <div className="mt-0.5 truncate text-slate-500">{signalStatus.tracking}</div>
            </div>
          )}
        </div>
      </div>

      {showFullDashboardButton&&subscriptionActive&&(
        <div className="flex justify-center border-b border-slate-800 bg-slate-950/30 px-5 py-4">
          <a href={`/asset/${asset.toLowerCase()}`}
            className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-500 px-6 py-3 text-sm font-bold text-white shadow-lg shadow-cyan-500/20 transition hover:from-cyan-600 hover:to-blue-600">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
            </svg>
            View Full Dashboard
          </a>
        </div>
      )}

      <div className="border-b border-slate-800 bg-slate-950/50 px-5 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Timeframe:</span>
          {TIMEFRAMES.map(tf=>(
            <button key={tf} type="button" onClick={()=>onTimeframeChange(tf)}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                timeframe===tf
                  ?'bg-cyan-500 text-white shadow-lg shadow-cyan-500/30'
                  :'bg-slate-800 text-slate-300 hover:bg-slate-700 hover:text-white'}`}>
              {tf.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-5 border-b border-slate-800 bg-slate-950/30 px-5 py-2 text-xs">
        <div className="flex items-center gap-1.5">
          <span style={{color:COLOR_UP}} className="text-base">▲</span>
          <span className="text-slate-400">BUY SIGNAL — Bullish Reversal</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span style={{color:COLOR_DOWN}} className="text-base">▼</span>
          <span className="text-slate-400">SELL SIGNAL — Bearish Reversal</span>
        </div>
      </div>

      <div className="relative h-[600px]">
        {sigLoading&&(
          <div className="absolute inset-0 z-20 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
            <div className="text-center">
              <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-cyan-500 border-r-transparent"/>
              <p className="mt-3 text-sm text-cyan-400">Loading chart data…</p>
            </div>
          </div>
        )}
        <div className={subscriptionActive?'h-full w-full':'pointer-events-none h-full w-full select-none blur-sm'}>
          <div ref={containerRef} className="h-full w-full"/>
        </div>
        {!subscriptionActive&&(
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-slate-950/55 backdrop-blur-[2px]">
            <div className="mx-4 max-w-md rounded-2xl border border-amber-500/30 bg-slate-900/95 p-6 text-center shadow-2xl shadow-black/30">
              <p className="text-xs font-semibold uppercase tracking-[0.25em] text-amber-300">Premium Charts</p>
              <h3 className="mt-2 text-xl font-semibold text-white">Subscribe to unlock full access</h3>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}