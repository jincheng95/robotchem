import React, {Component} from 'react';
import axios from 'axios';

import {Card, CardTitle, CardText, CardActions} from 'material-ui/Card';
import TextField from 'material-ui/TextField';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import Dialog from 'material-ui/Dialog';
import Loading from './loading';

import {Grid, Row, Col} from 'react-flexbox-grid';


export default class Access extends React.PureComponent {
  constructor(props) {
    super(props);
    this.state = {
      aboutDialogOpen: false,
      accessCodeRequired: true,
      accessCodeRejected: false,
      loading: false,
    };
    this.toggleDialog = this.toggleDialog.bind(this);
    this.handleCodeSubmitted = this.handleCodeSubmitted.bind(this);
  }

  toggleDialog() {
    this.setState({aboutDialogOpen: !this.state.aboutDialogOpen});
  }

  componentDidMount() {
    if(!!this.props.code) {
      this.handleCodeSubmitted();
    }
  }
  handleCodeSubmitted() {
    const { code, changeAccessCode, changeCalorimeterStatus, toggleLoading } = this.props;
    this.setState( {accessCodeRejected: false} );
    toggleLoading();
    changeAccessCode(code);
    axios.get('/api/status/?access_code=' + code)
      .then((response) => {
        toggleLoading();
        changeCalorimeterStatus(response.data);
      })
      .catch((error) => {
        toggleLoading();
        if(error.response){
          if(error.response.status == '403'){
            this.setState({accessCodeRejected: true});
            changeAccessCode(code, true);
          }
        }
      });
  }

  render() {
    const {code, isLoading, changeAccessCode} = this.props;
    if( code && isLoading ) {
      return (
        <Refreshing size={70} message="One moment please..."/>
      )
    }

    const dialogActions = [
      <FlatButton label="OK" onTouchTap={this.toggleDialog} />
    ];
    const enterAccessCode = (
      <div style={{minWidth: '80%', marginLeft: '10%', marginRight: '10%'}}>
          <TextField value={this.state.access_code} id="access-code-field"
                     style={{width: '100%'}} autoFocus
                     errorText={this.state.accessCodeRejected ? "Wrong access code! Please try again." : ""}
                     onChange={ (event) => changeAccessCode(event.target.value) }
                     onKeyPress={(event) => {
                       if(event.keyCode == 13) {this.handleCodeSubmitted();}
                     }}
          />
          <RaisedButton onTouchTap={this.handleCodeSubmitted}
            label="Go!" primary={true} style={{width: '100%'}}/>
        </div>
    );

    const main = (
      <Card style={{padding: '1em', marginTop: '2em'}}>
        <CardTitle title="Please enter your access code to continue."
                    subtitle="For security reasons, we must verify that you have the permission to control this device.">
        </CardTitle>
        <CardText>
          {this.state.accessCodeRequired && enterAccessCode}
        </CardText>
        <CardActions style={{marginLeft: '-0.75em'}}>
          <br/>
          <FlatButton label="About" onTouchTap={this.toggleDialog} />
        </CardActions>

        <Dialog open={this.state.aboutDialogOpen}
                title="About This Site" actions={dialogActions}
                onRequestClose={this.toggleDialog}>
          This website was created by Jin Cheng as part of a Robot Chemistry coursework at Imperial College London.<br/>
          It contains functionalities related to controlling a Differential Scanning Calorimeter, built by a group of five Fourth-Year students: Jin, Rebecca, Ker Fern, Hayley and Lily.
        </Dialog>
        <Loading open={this.state.loading}/>
      </Card>
    );

    return (
        <Grid>
          <Row>
            <Col xs={12}>
              {main}
            </Col>
          </Row>
        </Grid>
    );
  }
}