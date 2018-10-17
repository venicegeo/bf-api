/**
 * Copyright 2018, RadiantBlue Technologies, Inc.
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 * 
 *   http://www.apache.org/licenses/LICENSE-2.0
 * 
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 **/
package org.venice.beachfront.bfapi.services.converter;

import java.io.File;
import java.io.Reader;
import java.io.StringReader;

import org.geotools.feature.FeatureCollection;
import org.geotools.geojson.feature.FeatureJSON;
import org.geotools.geojson.geom.GeometryJSON;
import org.geotools.geopkg.FeatureEntry;
import org.geotools.geopkg.GeoPackage;
import org.opengis.feature.simple.SimpleFeatureType;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.exception.UserException;

/**
 * Implementation of the {@link AbstractConverter} class for GeoPackages.
 *
 * @version 2.0
 */
@Service
public class GeoPackageConverter extends AbstractConverter {

	/**
	 * Perform the actual conversion from GeoJSON to GeoPackage.
	 *
	 * @param geojson
	 *            A byte array containing GeoJSON data
	 * @return A byte array containing GPKG data
	 * @throws UserException
	 */
	public byte[] apply(byte[] geojson) throws UserException {
		byte[] result = null;

		try {
			String json = new String(geojson);
			GeometryJSON gjson = new GeometryJSON();

			Reader reader = new StringReader(json);
			FeatureJSON fjson = new FeatureJSON(gjson);

			FeatureCollection<?, ?> fc = fjson.readFeatureCollection(reader);
			SimpleFeatureType featureType = createSimpleFeatureType(fc, false);

			// DataStore
			final File inputFile = File.createTempFile("shorelines", ".gpkg");
			inputFile.delete();
			GeoPackage gpkg = new GeoPackage(inputFile);
			gpkg.init();
			gpkg.addCRS(4326);

			if (featureType.getGeometryDescriptor() != null) {
				FeatureEntry featureEntry = new FeatureEntry();
				gpkg.add(featureEntry, fcToSFC(fc, featureType));
				gpkg.createSpatialIndex(featureEntry);
			}

			// Return the results
			File gpkgFile = gpkg.getFile();
			result = java.nio.file.Files.readAllBytes(gpkgFile.toPath());
			gpkgFile.delete();
			gpkg.close();
		} catch (Exception e) {
			throw new UserException("Failed to export input to GeoPackage:" + e.getMessage(), e,
					org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR);
		}
		return result;
	}
}
