import React, {Component} from 'react';
import axios from 'axios';
import find from 'lodash/find';
import matches from 'lodash/matches';
import concat from 'lodash/concat';
import fill from 'lodash/fill';

import InfiniteScroll from 'react-infinite';
import HeightRuler from 'react-height';

import Run from '../components/run/run';
import Refreshing from '../components/refreshing';

export default class AllRunsContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      runs: [],
      heights: [],
      isInfiniteLoading: false,
      page: 0,
      has_more_pages: true,
    };
    this.loadPage = this.loadPage.bind(this);
    this.measureHeight = this.measureHeight.bind(this);
  }

  loadPage() {
    const {isInfiniteLoading, has_more_pages} = this.state;
    if( has_more_pages && !isInfiniteLoading ) {
      const {toggleLoading, code} = this.props;
      const page = this.state.page + 1;
      toggleLoading();

      const address = `/api/runs/?access_code=${code}&page=${page}`;
      this.setState({isInfiniteLoading: true}, () => {
        axios.get(address)
          .then((response) => {
            toggleLoading();
            this.setState({
              page: page,
              has_more_pages: parseInt(response.data.num_pages, 10) > page,
              runs: concat(this.state.runs, response.data.runs),
              heights: concat(this.state.heights, fill(response.data.runs.slice(), 270)),
              isInfiniteLoading: false
            });
          })
          .catch((error) => {
            toggleLoading();
            console.log(error.response);
            this.setState({isInfiniteLoading: false});
          })
      });
    }
  }
  measureHeight(index, height) {
    let heights = this.state.heights.slice();
    heights[index] = height;
  }

  render() {
    const {params} = this.props;
    if(!!params && !!params.run_id) {
      return (
        <Run {...this.props}
             run={find( this.state.runs, matches({ id: parseInt(this.props.params.run_id) }) )}
             expanded={true} />
      )
    }

    const loader = (
      <Refreshing size={60} zDepth={0} message="Loading..."/>
    );
    const end = (
      <div className="text-warning text-center">
        <hr/>
        You've reached the end of this list.
      </div>
    );
    const {runs, has_more_pages, heights} = this.state;

    return (
      <div style={{overflowY: 'hidden', margin: '-1em'}}>
        <InfiniteScroll useWindowAsScrollContainer={true}
                        elementHeight={heights.length == runs.length ? heights : fill(runs.slice(), 270)}
                        infiniteLoadBeginEdgeOffset={135}
                        onInfiniteLoad={this.loadPage}
                        loadingSpinnerDelegate={has_more_pages ? loader : <div/> } >
          {runs.map((run_data, index) => {
            return (
              <HeightRuler key={index} onHeightReady={this.measureHeight.bind(null, index)}>
                <div style={{margin: '1em'}}>
                  <Run {...this.props}
                       run={run_data}
                       expanded={!!run_data ? !run_data.is_finished : false} />
                </div>
              </HeightRuler>
            )
          })}
        </InfiniteScroll>
        {!has_more_pages && end}
      </div>
    )
  }
}