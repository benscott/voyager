import React, { Component } from 'react';

import { scaleLinear, scaleSequential } from "d3-scale";
import 'mapbox-gl/dist/mapbox-gl.css';
import { interpolateWarm } from "d3-scale-chromatic";
import { color } from "d3";


// Material UI
import 'fontsource-roboto';
import { MuiThemeProvider, createMuiTheme } from '@material-ui/core/styles';
import { Typography } from '@material-ui/core';
import { GetApp } from '@material-ui/icons';

import './App.scss';
import DateSlider from './components/DateSlider';
import VoyageSelect from './components/VoyageSelect';
import Map from './components/Map';
import Date from './components/Date';
import Occurrences from './components/Occurrences';
import { timestampToMonthYear, timestampToYear } from './utils'

// Voyager data
import voyages from './data/voyages';
import metadata from './data/metadata';
import occurrences from './data/occurrences';

const theme = createMuiTheme({
    palette: {
        type: 'dark',
        primary: {
            main: '#58616C'
        },
        text: {
            primary: "#ffffff",
            secondary: '#A0A7B4'
        },
        action: {
            active: '#58616C',
            hover: '#A0A7B4',
            selected: '#58616C',
        },
        background: {
            default: '#29323D',
            paper: '#29323D'
        }
    }
});

var myColor = scaleSequential().domain([1, voyages.length])
    .interpolator(interpolateWarm);


const vesselNames = {
    naturaliste: 'Naturaliste',
    adventure: 'HMS Adventure',
    vincennes: 'USS Vincennes',
    isabella: 'Isabella',
    alligator: 'Alligator',
    belgica: 'RV Belgica',
    beagle: 'HMS Beagle',
    resolution: 'HMS Resolution',
    discovery: 'HMS Discovery',
    challenger: 'HMS Challenger',
    favorite: 'La Favorite',
    'astrolabe+zelee': "L'Astrolabe and Zélée",
    investigator: 'HMS Investigator',
    hecla: 'HMS Hecla',
    scoresby: 'Scoresby',

}

for (let i in voyages) {
    voyages[i].metadata.color = color(myColor(i))
    voyages[i].metadata.vesselName = vesselNames[voyages[i].metadata.vessel]
}

const LINEAR_SCALE_RANGE = 5000;


export default class App extends Component {

    constructor(props) {
        super(props);
        this.state = {
            time: 0,
            isAnimated: false,
            selectedVoyage: -1,
            occurrences: []
        };
        this.timeToggle = this.timeToggle.bind(this)
        this.timeReset = this.timeReset.bind(this)
        this.timeStop = this.timeStop.bind(this)
        this.timeStart = this.timeStart.bind(this)
        this.timeUpdate = this.timeUpdate.bind(this)
        this.voyageUpdate = this.voyageUpdate.bind(this)
        this.linearScaleRange = LINEAR_SCALE_RANGE
        this.timeScale = this.getScaledTime()
        this.vesselNames = vesselNames
        this.years = {
            from: timestampToYear(metadata.minTimestamp),
            to: timestampToYear(metadata.maxTimestamp),
        }
    }

    getMinTimestamp() {
        if (this.state.selectedVoyage === -1) {
            return metadata.minTimestamp
        } else {
            return voyages[this.state.selectedVoyage].coordinates[0][2]
        }
    }

    getMaxTimestamp() {
        if (this.state.selectedVoyage === -1) {
            return metadata.maxTimestamp
        } else {
            // Get the index of the last element in the array
            const i = voyages[this.state.selectedVoyage].coordinates.length - 1
            return voyages[this.state.selectedVoyage].coordinates[i][2]
        }
    }

    getScaledTime() {
        return scaleLinear()
            .domain([
                this.getMinTimestamp(),
                this.getMaxTimestamp()
            ])
            .range([0, this.linearScaleRange]);
    }

    getOccurrences() {
        if (this.isVoyageSelected()) {
            const vessel = voyages[this.state.selectedVoyage].metadata.vessel
            return occurrences[vessel]
        }
        return []
    }

    getVoyages() {
        if (this.isVoyageSelected()) {
            return [voyages[this.state.selectedVoyage]]
        } else {
            return voyages
        }
    }

    isVoyageSelected() {
        return this.state.selectedVoyage !== -1
    }

    componentDidMount() {
        this._animate();
    }

    componentWillUnmount() {
        if (this._animationFrame) {
            this._animationStop();
        }
    }

    _animate() {
        const {
            maxTime = this.linearScaleRange,
            speed = (this.state.selectedVoyage === -1) ? 1 : 2
        } = this.props;

        if (this.state.time >= maxTime) {
            this.setState({
                time: 0
            });
        } else {
            this.setState({
                time: this.state.time + speed
            });
        }

        this._animationStart();

    }

    _animationStop() {
        window.cancelAnimationFrame(this._animationFrame);
        this.setState({
            isAnimated: false
        })
    }

    _animationStart() {
        this._animationFrame = window.requestAnimationFrame(this._animate.bind(this));
        this.setState({
            isAnimated: true
        })
    }

    // events

    timeReset() {
        this.setState({
            time: 0
        });
    }

    timeToggle() {
        if (this.state.isAnimated) {
            this._animationStop();
        } else {
            this._animationStart();
        }
    }

    timeStop() {
        this._animationStop();
    }

    timeStart() {
        this._animationStart();
    }

    timeUpdate(newTime) {
        this.setState({
            time: newTime
        });
    }

    voyageUpdate(value) {
        // Voyage selection has changed - update
        this.setState({
            selectedVoyage: value
        });
        this.timeReset();
        // I think this is the best UX
        this.timeStart();
    }


    getScaleLabels() {

        const minDate = timestampToMonthYear(this.getMinTimestamp());
        const maxDate = timestampToMonthYear(this.getMaxTimestamp())

        if (this.state.selectedVoyage === -1) {
            return {
                min: minDate.year,
                max: maxDate.year
            }
        } else {
            return {
                min: minDate.month + ' ' + minDate.year,
                max: maxDate.month + ' ' + maxDate.year
            }
        }

    }

    getHeader() {
        // []
        const header = {}
        if (this.isVoyageSelected()) {
            const voyage = voyages[this.state.selectedVoyage]
            header.title = 'Voyage of ' + voyage.metadata.vesselName
            header.subtitle = voyage.metadata.year_from + ' - ' + voyage.metadata.year_to
        } else {
            header.title = 'Voyages of discovery'
            header.subtitle = 'Voyages of scientific exploration ' + this.years.from + ' - ' + this.years.to
        }

        return header

    }

    render() {
        const {
            voyageMetadata = voyages.map(r => r.metadata),
            voyagesData = this.getVoyages(),
            header = this.getHeader(),
            timeScale = this.getScaledTime(),
            scaleLabels = this.getScaleLabels(),
            isVoyageSelected = this.isVoyageSelected(),
            timestamp = timeScale.invert(this.state.time),
            occurrences = this.getOccurrences(),
        } = this.props;

        return (
            <MuiThemeProvider theme={theme}>

                <div id="title">
                    <Typography component="h1" variant="h3" color="textPrimary">
                        {header.title}
                    </Typography>
                    <Typography component="h2" variant="h6" color="textSecondary">
                        {header.subtitle}
                    </Typography>
                </div>

                <Map
                    time={this.state.time}
                    voyages={voyagesData}
                    timeScale={timeScale}
                />

                <VoyageSelect
                    voyageUpdate={this.voyageUpdate}
                    voyageMetadata={voyageMetadata}
                    selectedVoyage={this.state.selectedVoyage}
                />


                <div id="info-panel" className="panel">

                    {isVoyageSelected ? (
                        <Occurrences
                            occurrences={occurrences}
                            timeStop={this.timeStop}
                            isAnimated={this.state.isAnimated}
                            time={this.state.time}
                            timeScale={timeScale}
                            timeUpdate={this.timeUpdate}
                        />

                    ) : (
                            <div>
                                <Typography component="h2" variant="h6" color="textPrimary">
                                    How it works
                            </Typography>

                                <Typography color="textSecondary" variant="body1" paragraph={true}>
                                    This map displays historical maritime voyages which collected biodiversity specimens. These specimens are now deposited in institutions around the world, this map shows where and when they were collected.
                            </Typography>

                                <Typography color="textSecondary" variant="body1" paragraph={true}>
                                    Voyage routes have been identified using historical <a rel="noopener noreferrer" target="_blank" title="ICOADS and OldWeather" href="https://github.com/benscott/voyager">ship log data</a>. Specimens have been identified from GBIF, by geotemporal covariance with each route.
                            </Typography>

                                <Typography color="textSecondary" variant="body1" paragraph={true}>
                                    To view collected specimens, please <span color="textPrimary">select a voyage</span> above.
                            </Typography>

                                <Typography color="textSecondary" variant="body1" paragraph={true}>
                                    <a id="data-download" target="_blank" rel="noopener noreferrer" color="textSecondary" title="Data sources" href="https://github.com/benscott/voyager/output/dwca"><GetApp /> Get the data (DwC-A)</a>
                                </Typography>
                            </div>
                        )}

                </div>

                <Date
                    time={timestamp}
                />

                <DateSlider
                    time={this.state.time}
                    isAnimated={this.state.isAnimated}
                    linearScaleRange={this.linearScaleRange}
                    scaleLabels={scaleLabels}
                    // timeScale={timeScale}
                    // Bubble up events
                    timeToggle={this.timeToggle}
                    timeStart={this.timeStart}
                    timeStop={this.timeStop}
                    timeReset={this.timeReset}
                    timeUpdate={this.timeUpdate}

                />


            </MuiThemeProvider>
        );

    }
}




// export function renderToDOM(container) {
//     render(<App />, container);
// }