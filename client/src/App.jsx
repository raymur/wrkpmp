import { useEffect, useState, useRef, Fragment, useDeferredValue} from 'react'
import './App.css'
import Axios from 'axios';

const get_greenhouse_job_url = (company, job) => `https://job-boards.greenhouse.io/${company}/jobs/${job}`
const get_greenhouse_company_url = (company) => `https://job-boards.greenhouse.io/${company}`

const COMPANIES = 'companies';
const TITLES = 'titles';
const LOCATIONS = 'locations';
const REMOTE = 'remote';
const US = 'us'



function App() {
  
  const [loadMoreState, setLoadMoreState] = useState('NORMAL')
  const [jobs, setJobs] = useState([]);
  const [jobQuery, setJobQuery] = useState({
    companies: localStorage.getItem(COMPANIES) || '', 
    titles: localStorage.getItem(TITLES) || '', 
    locations:localStorage.getItem(LOCATIONS) || '', 
    remote: localStorage.getItem(REMOTE) == 'true'? true : false, 
    us: localStorage.getItem(US) == 'true' ? true : false, 
    page: 0
  });
  const companyFilter = useDeferredValue(jobQuery.company);
  const titleFilter = useDeferredValue(jobQuery.titles);
  const locationFilter = useDeferredValue(jobQuery.locations);
  const remoteFilter = useDeferredValue(jobQuery.remote);
  const usFilter = useDeferredValue(jobQuery.us);
  const page = useRef(jobQuery.page);// should this be using state instead???
  const delay = useRef(0)

  useEffect(()=>{
    Axios.get('/api/ping').then((resp)=> console.log(resp.data) )
  }, [])

  useEffect(()=>{
    const jobFilterTimeout = setTimeout(getJobs, delay.current)
    delay.current = 500
    return () => clearTimeout(jobFilterTimeout)
  },[jobQuery])

  const getJobs = () =>{
    const requestData = jobQuery 
    const headers = {headers: {'Content-Type': 'application/json'}}
    Axios.post('/api/get_jobs', requestData, headers)
      .then((resp)=> {
        setLoadMoreState(resp.data.length < 100 ? 'DISABLED': 'NORMAL')
        if (requestData.page){
          setJobs([...jobs, ...resp.data])
        }else {
          setJobs(resp.data)
        }
      }).catch(()=>setJobs([]))
    storePrefs() 
  }

  const storePrefs = () => {
    [TITLES, LOCATIONS, REMOTE, US].forEach(v=>
      localStorage.setItem(v, jobQuery[v])
    )
  }

  const onFilterChange = (o) => {
    if (o.remote != null || o.us !=null ){
      delay.current = 0 // 0 delay for checkbox
    }
    page.current = 0
    setJobQuery({...jobQuery, ...o, page: page.current})
  }

  const loadMoreJobs = () => {
    page.current++
    delay.current = 0
    setLoadMoreState('LOADING')
    setJobQuery({...jobQuery, page: page.current})
  }

  return (
    <>
      <div className='header-div'>
      <h1 >WRK PMP</h1>
      <h5 >help</h5>

      </div>
        <div className='job-grid'>
          <span >company filter: <input onChange={e => onFilterChange({companies: e.target.value})} value={companyFilter}></input></span>
          <span >title filter: <input onChange={e => onFilterChange({titles: e.target.value})} value={titleFilter}></input></span>
          <span >
            <div>filter remote jobs:
              <input 
              type='checkbox' 
              onChange={e => onFilterChange({remote: e.target.checked})} 
              checked={remoteFilter}>
              </input>
            </div>
            <div>filter US jobs:
              <input 
              type='checkbox' 
              onChange={e => onFilterChange({us: e.target.checked})} 
              checked={usFilter}>
              </input>
            </div>

            location filter: <input onChange={e => onFilterChange({ locations: e.target.value})} value={locationFilter}></input>
          
          </span>

    
      {
        jobs?.map((job, i)=> 
          <Fragment key={job[0]}>
            <a key={job[3]+'_comp'} href={get_greenhouse_company_url(job[3])} target="_blank" className={ i%2 ? 'odd' : 'even'}>
              {job[3]}
            </a>
            <a key={job[3]+'_job'} href={get_greenhouse_job_url(job[3], job[0])} target="_blank" className={ i%2 ? 'odd' : 'even'}>
              {job[1]}
            </a>
            <span key={job[3]+'_loc'} className={ i%2 ? 'odd' : 'even'}>
              {job[2]}
            </span>
            </Fragment>
        )
      }
        </div>
        <div className='load-more'>
        {loadMoreState == 'DISABLED' ? 
  <p>refine filters to show more jobs</p>
        :

          <button  onClick={loadMoreJobs} disabled={ loadMoreState == 'LOADING'} >
            load more
            {loadMoreState == 'LOADING' && '🔃'}
          </button>
}
</div>

    </>
  )
}

export default App
