"""Sample this process and host resources; Windows GPU counters need no GPU SDK."""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import math
import os
import platform
import re
import threading
import time


def hardware_info(psutil):
    info={'cpu':platform.processor(),'physical_cores':psutil.cpu_count(logical=False),'logical_processors':psutil.cpu_count(),'ram_gib':round(psutil.virtual_memory().total/2**30,2),'gpu_adapters':[]}
    if os.name=='nt':
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'HARDWARE\DESCRIPTION\System\CentralProcessor\0') as key:
                info['cpu']=winreg.QueryValueEx(key,'ProcessorNameString')[0].strip()
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,r'SYSTEM\CurrentControlSet\Control\Video') as root:
                for i in range(winreg.QueryInfoKey(root)[0]):
                    name=winreg.EnumKey(root,i)
                    try:
                        with winreg.OpenKey(root,name+r'\0000') as key:
                            adapter=winreg.QueryValueEx(key,'DriverDesc')[0]
                            if adapter not in info['gpu_adapters']:info['gpu_adapters'].append(adapter)
                    except OSError:pass
        except OSError as error:info['inventory_note']=str(error)
    return info


def aggregate_engines(items,pid):
    """Sum processes on each hardware engine, then report the busiest engine."""
    total={};own={}
    for name,value in items:
        match=re.match(r'pid_(\d+)_(luid_.+?_phys_\d+_eng_\d+_engtype_.+)',name,re.I)
        if not match or not math.isfinite(value):continue
        engine=match[2].lower();total[engine]=total.get(engine,0)+max(0,value)
        if int(match[1])==pid:own[engine]=own.get(engine,0)+max(0,value)
    if not total:return None,None
    return min(100,max(total.values())),min(100,max(own.values(),default=0))


class WindowsGPU:
    def __init__(self,pid):
        self.pid=pid;self.query=None;self.counters={};self.errors={};self.available=False
        if os.name!='nt':
            self.errors['backend']='Windows PDH GPU counters are unavailable on this platform.';return
        self.dll=ctypes.WinDLL('pdh')
        self.dll.PdhOpenQueryW.argtypes=[wintypes.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)]
        self.dll.PdhOpenQueryW.restype=wintypes.LONG
        self.dll.PdhAddEnglishCounterW.argtypes=[ctypes.c_void_p,wintypes.LPCWSTR,ctypes.c_size_t,ctypes.POINTER(ctypes.c_void_p)]
        self.dll.PdhAddEnglishCounterW.restype=wintypes.LONG
        self.dll.PdhCollectQueryData.argtypes=[ctypes.c_void_p];self.dll.PdhCollectQueryData.restype=wintypes.LONG
        self.dll.PdhGetFormattedCounterArrayW.argtypes=[ctypes.c_void_p,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),ctypes.POINTER(wintypes.DWORD),ctypes.c_void_p]
        self.dll.PdhGetFormattedCounterArrayW.restype=wintypes.LONG
        self.dll.PdhCloseQuery.argtypes=[ctypes.c_void_p]
        self.query=ctypes.c_void_p()
        status=self.dll.PdhOpenQueryW(None,0,ctypes.byref(self.query))
        if status:
            self.errors['query']=f'PDH error 0x{status&0xffffffff:08x}';self.query=None;return
        for key,path in {
            'engines':r'\GPU Engine(*)\Utilization Percentage',
            'adapter_dedicated':r'\GPU Adapter Memory(*)\Dedicated Usage',
            'adapter_shared':r'\GPU Adapter Memory(*)\Shared Usage',
            'process_dedicated':r'\GPU Process Memory(*)\Dedicated Usage',
            'process_shared':r'\GPU Process Memory(*)\Shared Usage',
        }.items():
            counter=ctypes.c_void_p()
            status=self.dll.PdhAddEnglishCounterW(self.query,path,0,ctypes.byref(counter))
            if status:self.errors[key]=f'PDH error 0x{status&0xffffffff:08x}'
            else:self.counters[key]=counter
        self.dll.PdhCollectQueryData(self.query)

    def items(self,key):
        if key not in self.counters:return None
        class Value(ctypes.Structure):
            _fields_=[('status',wintypes.DWORD),('value',ctypes.c_double)]
        class Item(ctypes.Structure):
            _fields_=[('name',wintypes.LPWSTR),('counter',Value)]
        size=wintypes.DWORD();count=wintypes.DWORD()
        status=self.dll.PdhGetFormattedCounterArrayW(self.counters[key],0x200,ctypes.byref(size),ctypes.byref(count),None)
        if (status&0xffffffff)!=0x800007d2 or not size.value:return None
        buffer=ctypes.create_string_buffer(size.value)
        status=self.dll.PdhGetFormattedCounterArrayW(self.counters[key],0x200,ctypes.byref(size),ctypes.byref(count),buffer)
        if status:
            self.errors[key]=f'PDH read error 0x{status&0xffffffff:08x}';return None
        items=ctypes.cast(buffer,ctypes.POINTER(Item))
        values=[(items[i].name,items[i].counter.value) for i in range(count.value) if items[i].counter.status in (0,1)]
        return values or None

    def sample(self):
        fields=['gpu_system_busiest_engine_percent','gpu_process_busiest_engine_percent','gpu_system_dedicated_mib','gpu_system_shared_mib','gpu_process_dedicated_mib','gpu_process_shared_mib']
        result=dict.fromkeys(fields)
        if not self.query:return result
        self.dll.PdhCollectQueryData(self.query)
        engines=self.items('engines')
        if engines:
            system,process=aggregate_engines(engines,self.pid)
            result['gpu_system_busiest_engine_percent']=system;result['gpu_process_busiest_engine_percent']=process
            self.available=system is not None
        for counter,field in [('adapter_dedicated','gpu_system_dedicated_mib'),('adapter_shared','gpu_system_shared_mib'),('process_dedicated','gpu_process_dedicated_mib'),('process_shared','gpu_process_shared_mib')]:
            items=self.items(counter)
            if items:
                result[field]=sum(max(0,value) for name,value in items if not counter.startswith('process') or name.lower().startswith(f'pid_{self.pid}_'))/2**20
        return result

    def close(self):
        if self.query:self.dll.PdhCloseQuery(self.query);self.query=None


def sample_stats(samples,key):
    values=[(s[key],s.get('interval_seconds',0)) for s in samples if s.get(key) is not None and math.isfinite(s[key])]
    if not values:return {'mean':None,'peak':None,'samples':0}
    weight=sum(w for _,w in values)
    mean=sum(v*w for v,w in values)/weight if weight else sum(v for v,_ in values)/len(values)
    return {'mean':round(mean,3),'peak':round(max(v for v,_ in values),3),'samples':len(values)}


class ResourceMonitor:
    def __init__(self,interval=.25):
        import psutil
        self.psutil=psutil;self.interval=interval;self.process=psutil.Process();self.logical=psutil.cpu_count() or 1
        self.gpu=WindowsGPU(self.process.pid);self.samples=[];self.phases=[];self.phase='setup';self.lock=threading.Lock();self.stop_event=threading.Event()
        self.started=time.perf_counter();self.last=self.started;self.last_cpu=self.cpu_seconds();self.initial_cpu=self.last_cpu
        self.thread=threading.Thread(target=self._run,daemon=True,name='vision-resource-sampler')

    def cpu_seconds(self):
        c=self.process.cpu_times();return c.user+c.system

    def start(self):
        self.thread.start();return self

    def _run(self):
        self.psutil.cpu_percent(interval=None)
        while not self.stop_event.is_set():
            self._sample()
            self.stop_event.wait(self.interval)
        self._sample()

    def _sample(self):
        now=time.perf_counter();cpu=self.cpu_seconds();elapsed=now-self.last
        raw=(cpu-self.last_cpu)/elapsed*100 if elapsed>.001 else None
        record={'t':round(now-self.started,6),'phase':self.phase,'interval_seconds':elapsed,'process_cpu_percent_one_core':raw,'process_cpu_percent_machine':raw/self.logical if raw is not None else None,'process_rss_mib':self.process.memory_info().rss/2**20,'system_cpu_percent':self.psutil.cpu_percent(interval=None),'system_ram_percent':self.psutil.virtual_memory().percent,**self.gpu.sample()}
        self.last=now;self.last_cpu=cpu
        with self.lock:self.samples.append(record)

    @contextmanager
    def measure(self,name):
        old=self.phase;self.phase=name;start=time.perf_counter();cpu=self.cpu_seconds();rss=self.process.memory_info().rss/2**20
        measurement={'name':name}
        try:yield measurement
        finally:
            end=time.perf_counter();cpu_delta=max(0,self.cpu_seconds()-cpu)
            with self.lock:records=[s for s in self.samples if start-self.started<=s['t']<=end-self.started]
            wall=end-start
            measurement.update({'wall_seconds':round(wall,6),'cpu_seconds':round(cpu_delta,6),'process_cpu_percent_one_core_mean':round(cpu_delta/wall*100,3),'process_cpu_percent_machine_mean':round(cpu_delta/wall/self.logical*100,3),'process_rss_mib_peak_observed':round(max([rss,self.process.memory_info().rss/2**20]+[s['process_rss_mib'] for s in records]),3),'sample_count':len(records)})
            for key in ['process_cpu_percent_machine','system_cpu_percent','gpu_system_busiest_engine_percent','gpu_process_busiest_engine_percent','gpu_system_dedicated_mib','gpu_process_dedicated_mib','gpu_process_shared_mib']:
                measurement[key+'_sampled']=sample_stats(records,key)
            self.phases.append(measurement);self.phase=old

    def finish(self):
        self.stop_event.set();self.thread.join(timeout=5)
        self.gpu.close()
        duration=time.perf_counter()-self.started;cpu=self.cpu_seconds()-self.initial_cpu
        metrics={'sampling_interval_seconds_requested':self.interval,'observed_samples':len(self.samples),'measured_wall_seconds':round(duration,3),'process_cpu_seconds':round(cpu,3),'process_cpu_percent_one_core_mean':round(cpu/duration*100,3),'process_cpu_percent_machine_mean':round(cpu/duration/self.logical*100,3),'phases':self.phases,'gpu_counter_backend':'Windows PDH / busiest hardware engine','gpu_counters_available':self.gpu.available,'gpu_counter_errors':self.gpu.errors,'definitions':{'cpu_one_core':'100% equals one logical CPU; multithreaded values can exceed 100%.','cpu_machine':'Percentage of all logical CPU capacity.','rss':'Resident process memory; sampled peaks can miss sub-interval spikes.','gpu_system':'Busiest hardware engine across all applications; not attributable to this model.','gpu_process':'Busiest engine attributed to the benchmark process by Windows. Missing PID with valid counters is zero; unavailable counters are null.','timing':'Phases are instrumented and include monitoring overhead. GPU counters use the driver sampling window. No uninstrumented control or warmup is run.'}}
        for key in ['process_cpu_percent_machine','process_rss_mib','system_cpu_percent','system_ram_percent','gpu_system_busiest_engine_percent','gpu_process_busiest_engine_percent','gpu_system_dedicated_mib','gpu_system_shared_mib','gpu_process_dedicated_mib','gpu_process_shared_mib']:
            metrics[key+'_sampled']=sample_stats(self.samples,key)
        metrics['hardware']=hardware_info(self.psutil);metrics['psutil_version']=self.psutil.__version__
        return metrics,self.samples


class FirstTokenClock:
    """Transformers streamer hook: ignore the prompt, time the first new token."""
    def __init__(self,clock=time.perf_counter):
        self.clock=clock;self.started=clock();self.first_token_seconds=None;self.prompt_seen=False

    def put(self,value):
        if not self.prompt_seen:
            self.prompt_seen=True
        elif self.first_token_seconds is None:
            self.first_token_seconds=self.clock()-self.started

    def end(self):
        pass
