import React, { Component } from 'react';
import DeckGL from '@deck.gl/react';
import { AmbientLight, PointLight, LightingEffect } from '@deck.gl/core';
import { LineLayer, ScatterplotLayer } from '@deck.gl/layers';
import { StaticMap } from 'react-map-gl';
import { TripsLayer } from '@deck.gl/geo-layers';
import { scaleLinear } from "d3-scale";
import 'mapbox-gl/dist/mapbox-gl.css';
import { FixedSizeList as List } from 'react-window';
import { DropdownList } from 'react-widgets'

import routes from './data/expeditions';
import metadata from './data/metadata';
import './App.scss';

console.log(metadata)

// console.log(routes)

// https://github.com/visgl/deck.gl/blob/master/examples/website/trips/app.js
// Updated, this version is based on: 
// https://github.com/visgl/deck.gl/blob/e0d9a2528db452b6b47353dbe53f94e6b478d418/examples/website/trips/app.js

const MAPBOX_TOKEN = 'pk.eyJ1IjoiYmVuLXZveWFnZXIiLCJhIjoiY2tjOWIyODg0MGF3eTJ4bGsycDMwM3hndiJ9.6DY1ziPMXfA5k765IG3K7w'

// Viewport settings
const INITIAL_VIEW_STATE = {
    longitude: -3,
    latitude: 40.72,
    zoom: 8,
    pitch: 45,
    bearing: 0
};

// // Source data CSV
// const DATA_URL = {
//     TRIPS: 'https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/trips/trips-v7.json' // eslint-disable-line
// };

const timeScale = scaleLinear() //scaleLinear from d3-scale
    .domain([
        metadata.minTimestamp,
        metadata.maxTimestamp
    ])
    .range([0, 10000]);


// const x = routes.coordinates.map(t => timeScale(t[2]));
// console.log(routes.coordinates.map(t => [t[0], t[1]]));

// Source data CSV
const DATA_URL = {
    BUILDINGS:
        'https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/trips/buildings.json', // eslint-disable-line
    TRIPS: 'https://raw.githubusercontent.com/visgl/deck.gl-data/master/examples/trips/trips-v7.json' // eslint-disable-line
};

const ambientLight = new AmbientLight({
    color: [255, 255, 255],
    intensity: 1.0
});

const pointLight = new PointLight({
    color: [255, 255, 255],
    intensity: 2.0,
    position: [-74.05, 40.7, 8000]
});

const lightingEffect = new LightingEffect({ ambientLight, pointLight });

const material = {
    ambient: 0.1,
    diffuse: 0.6,
    shininess: 32,
    specularColor: [60, 64, 70]
};

const DEFAULT_THEME = {
    buildingColor: [74, 80, 87],
    trailColor0: [253, 128, 93],
    trailColor1: [23, 184, 190],
    material,
    effects: [lightingEffect]
};


const Row = ({ index, style }) => (
    <div style={style}>Row {index}</div>
);

const voyages = [
    {
        id: 'all',
        title: 'All voyages',
        date: '1800-1900',
    },
    {
        id: 'beagle-1831',
        title: 'HMS Beagle',
        date: '1831–1836',
        subtitle: 'Second voyage of the Beagle',
    },
    {
        id: 'beagle-1832',
        title: 'La Favorite',
        date: '1831–18XX',
        subtitle: 'La Favorite voyage'
    }
]

let ListItem = ({ item }) => (
    <span>
        <strong>{item.title}</strong>
        {" " + item.date}
    </span>
);

export default class App extends Component {

    constructor(props) {
        super(props);
        this.state = {
            time: 0,
            voyage: voyages[0]
        };
    }

    componentDidMount() {
        this._animate();
    }

    componentWillUnmount() {
        if (this._animationFrame) {
            window.cancelAnimationFrame(this._animationFrame);
        }
    }

    _animate() {
        const {
            numDays = 1800,
        } = this.props;

        if (this.state.time >= 10000) {
            this.setState({
                time: 0
            });
        } else {
            this.setState({
                time: this.state.time + 1
            });
        }
        this._animationFrame = window.requestAnimationFrame(this._animate.bind(this));
    }

    _renderLayers() {
        const {
            trips = routes,
            // trips = data_trips,
            trailLength = 100,
        } = this.props;

        return [
            new TripsLayer({
                id: 'route',
                data: trips,
                // getPath: d => d.path,
                // getTimestamps: d => d.timestamps,
                getPath: d => d.coordinates.map(t => [t[0], t[1]]),
                getTimestamps: d => d.coordinates.map(t => timeScale(t[2])),
                getColor: [253, 128, 93],
                opacity: 0.8,
                widthMinPixels: 3,
                rounded: true,
                trailLength,
                currentTime: this.state.time,
                shadowEnabled: true
            }),
        ]

    }

    render() {
        const {
            initialViewState = INITIAL_VIEW_STATE,
            mapStyle = 'mapbox://styles/mapbox/dark-v9',
            theme = DEFAULT_THEME,
            row = Row,
            isVoyage = this.state.voyage.id != 'all'
        } = this.props;

        return (
            <div>
                <DeckGL
                    layers={this._renderLayers()}
                    effects={theme.effects}
                    initialViewState={initialViewState}
                    controller={true}
                >
                    <StaticMap
                        reuseMaps
                        mapStyle={mapStyle}
                        preventStyleDiffing={true}
                        mapboxApiAccessToken={MAPBOX_TOKEN}
                    />
                </DeckGL>
                <DropdownList
                    data={voyages}
                    textField='voyage'
                    itemComponent={ListItem}
                    value={this.state.voyage.title}
                    onChange={value => this.setState({ voyage: value })}
                    ref={React.createRef()}
                />
                {isVoyage && (
                    <List height={100} itemCount={1000} itemSize={35} width={300}>
                        {row}
                    </List>
                )}
            </div >
        );

    }
}




// export function renderToDOM(container) {
//     render(<App />, container);
// }