import React, {Component} from 'react';
import axios from 'axios';

import Run from '../components/run/run';
import Refreshing from '../components/refreshing';

export default class RunContainer extends Component {
  constructor(props, context) {
    super(props, context);
    this.state = {
      run: null,
      isLoading: true,
    };
  }

  componentDidMount() {
    const {toggleLoading, code, params} = this.props;
    toggleLoading();
    const {run_id} = params;
    axios.get(`/api/run/${run_id}/?access_code=${code}`)
      .then((response) => {
        toggleLoading();
        this.setState({run: response.data, isLoading: false});
      })
      .catch((error) => {
        console.log(!!error.response ? error.response : error);
      });
  }

  render() {
    const {isLoading, run} = this.state;

    if(isLoading) {
      return (
        <Refreshing size={100} message="Loading..."/>
      )
    }

    return (
      <div>
        <Run {...this.props} run={run} expanded={true} />
      </div>
    );
  }
}