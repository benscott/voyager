import React, { Component } from 'react';
import DeckGL from '@deck.gl/react';
import { AmbientLight, PointLight, LightingEffect } from '@deck.gl/core';
import { StaticMap } from 'react-map-gl';
import { TripsLayer } from '@deck.gl/geo-layers';

const MAPBOX_TOKEN = 'pk.eyJ1IjoiYmVuLXZveWFnZXIiLCJhIjoiY2tjOWIyODg0MGF3eTJ4bGsycDMwM3hndiJ9.6DY1ziPMXfA5k765IG3K7w'

// Viewport settings
const INITIAL_VIEW_STATE = {
    longitude: -3,
    latitude: 40.72,
    zoom: 1,
    pitch: 35,
    bearing: 0,
    minZoom: 1,
    maxZoom: 10
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
    buildingColor: [180, 80, 87],
    trailColor0: [253, 128, 93],
    trailColor1: [23, 184, 190],
    material,
    effects: [lightingEffect]
};

export default class Map extends Component {

    // Below this, move to map
    _getColor(d) {
        return [
            d.metadata.color.r,
            d.metadata.color.g,
            d.metadata.color.b
        ];
        // return [23, 184, 190];
    }

    _renderLayers() {
        const {
            trailLength = 1000,
        } = this.props;

        return [
            new TripsLayer({
                id: 'voyages',
                data: this.props.voyages,
                getPath: d => d.coordinates.map(t => [t[0], t[1]]),
                getTimestamps: d => d.coordinates.map(t => this.props.timeScale(t[2])),
                getColor: this._getColor,
                opacity: 0.8,
                widthMinPixels: 2,
                rounded: true,
                trailLength,
                currentTime: this.props.time,
                shadowEnabled: true,
                wrapLongitude: true,
                pickable: true,
                // pointRadiusMinPixels: 1
            }),
        ]

    }

    render() {
        const {
            initialViewState = INITIAL_VIEW_STATE,
            // mapStyle = 'mapbox://styles/ben-voyager/ckcox4wk30nm11io3dnlcoemw',

            mapStyle = 'mapbox://styles/ben-voyager/ckcyu7d7e26p31imni4vw8x4f',
            theme = DEFAULT_THEME,
        } = this.props;

        return (
            <DeckGL
                layers={this._renderLayers()}
                effects={theme.effects}
                initialViewState={initialViewState}
                controller={true}
                getTooltip={({ object }) => object && (object.metadata.vesselName)}
                height="100vh"
                width="100vw"
            >
                <StaticMap
                    reuseMaps
                    mapStyle={mapStyle}
                    preventStyleDiffing={true}
                    mapboxApiAccessToken={MAPBOX_TOKEN}
                    height="100%"
                    width="100%"
                />
            </DeckGL >
        );

    }
}