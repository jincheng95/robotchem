import React, {Component} from 'react';
import axios from 'axios';

import {Card, CardTitle, CardMedia, CardText, CardActions} from 'material-ui/Card';
import TextField from 'material-ui/TextField';
import RaisedButton from 'material-ui/RaisedButton';
import FlatButton from 'material-ui/FlatButton';
import Dialog from 'material-ui/Dialog';
import Loading from './loading';

import {Grid, Row, Cell} from 'react-inline-grid';
import Center from 'react-center';

export default class Access extends Component {
  constructor(props) {
    super(props);
    this.state = {
      access_code: '',
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

  handleCodeSubmitted() {
    const { changeAccessCode, changeCalorimeterStatus, toggleLoading } = this.props;
    this.setState({accessCodeRejected: false});
    toggleLoading();
    const code = this.state.access_code;
    axios.get('/api/status/?access_code=' + code)
      .then((response) => {
        changeCalorimeterStatus(response.data);
        changeAccessCode(code);
        toggleLoading();
      })
      .catch((error) => {
        toggleLoading();
        if(error.response){
          if(error.response.status == '403'){
            this.setState({accessCodeRejected: true});
          }
        }
      });
  }

  render() {
    const dialogActions = [
      <FlatButton label="OK" onTouchTap={this.toggleDialog} />
    ];

    const enterAccessCode = (
      <div>
          <TextField type="password" value={this.state.access_code} id="access-code-field"
                     style={{width: '70%'}}
                     errorText={this.state.accessCodeRejected ? "Wrong access code! Please try again." : ""}
                     onChange={(event) => this.setState({access_code: event.target.value})}/>
          <RaisedButton onClick={this.handleCodeSubmitted}
            label="Go!" primary={true} style={{width: '70%'}}/>
        </div>
    );
    const main = (
      <Card style={{padding: '3em 3em 1em 3em', marginTop: '2em'}}>
        <CardTitle title="Please enter your access code to continue."
                    subtitle="For security reasons, we must verify that you have the permission to control this device.">
        </CardTitle>
        <CardText>
          {this.state.accessCodeRequired && enterAccessCode}
        </CardText>
        <CardActions style={{marginLeft: '-0.75em'}}>
          <br/>
          <FlatButton label="About" onClick={this.toggleDialog} />
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
          <Row is="center">
            <Cell is="middle 9 tablet-10 phone-11">
              {main}
            </Cell>
          </Row>
        </Grid>
    );
  }
}