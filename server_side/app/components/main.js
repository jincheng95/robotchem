import React, {Component} from 'react';
import AppBar from 'material-ui/AppBar';
import IconButton from 'material-ui/IconButton';
import Dashboard from 'material-ui/svg-icons/action/dashboard';

const TitleBar = (props) => (
    <AppBar title="RoboChem"
        titleStyle={{fontFamily: "'Patua One', cursive", fontSize: "200%"}}
        iconElementLeft={<IconButton> <Dashboard/> </IconButton>}/>
);

export default class Main extends Component {
    render() {
        return (
            <div>
                <TitleBar />
            </div>
        );
    }
}