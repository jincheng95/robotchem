import React, {Component} from 'react';
import axios from 'axios';
import find from 'lodash/find';
import matches from 'lodash/matches';

import Run from '../components/run/run';
import Refreshing from '../components/refreshing';

export default class AllRunsContainer extends Component {
  constructor(props) {
    super(props);
    this.state = {
      runs: [],
      isLoading: true,
    }
  }

  componentDidMount() {
    const {toggleLoading, code} = this.props;
    toggleLoading();
    axios.get('/api/runs/?access_code=' + code)
      .then((response) => {
        toggleLoading();
        this.setState({runs: response.data, isLoading: false});
      })
      .catch((error) => {
        toggleLoading();
        console.log(error.response);
      })
  }

  render() {
    if(this.state.isLoading) {
      return <Refreshing size={60} zDepth={0} message="One moment please..."/>
    }

    return (
      <div>
        {(!!this.props.params && !!this.props.params.run_id)
          ? <Run {...this.props}
               run={find( this.state.runs, matches({ id: parseInt(this.props.params.run_id) }) )}
               expanded={true} />
          : <div>{this.state.runs.map((run_data, index) => {
              return (
                <Run {...this.props}
                     key={index} run={run_data}
                     expanded={!run_data.is_finished}
                />
              )
            })}</div>
        }
      </div>
    )
  }
}