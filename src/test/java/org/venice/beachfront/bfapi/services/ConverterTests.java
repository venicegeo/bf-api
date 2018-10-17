package org.venice.beachfront.bfapi.services;

import java.io.File;
import java.io.IOException;

import org.apache.commons.io.IOUtils;
import org.junit.Before;
import org.junit.Test;
import org.venice.beachfront.bfapi.model.exception.UserException;
import org.venice.beachfront.bfapi.services.converter.GeoPackageConverter;
import org.venice.beachfront.bfapi.services.converter.ShapefileConverter;

/**
 * Tests data conversion logic.
 * <p>
 * At this point, there's no tests that validate these outputs. This merely attempts to resolve issues where crashes
 * occur due to irregular datasets (such as detections without any geometry)
 */
public class ConverterTests {
	private GeoPackageConverter geoPackageConverter = new GeoPackageConverter();
	private ShapefileConverter shapefileConverter = new ShapefileConverter();
	private String emptyGeoJson;
	private String shorelinesGeoJson;

	@Before
	public void setup() throws IOException {
		emptyGeoJson = IOUtils.toString(
				getClass().getClassLoader().getResourceAsStream(String.format("%s%s%s", "converter", File.separator, "empty.geojson")),
				"UTF-8");
		shorelinesGeoJson = IOUtils.toString(getClass().getClassLoader()
				.getResourceAsStream(String.format("%s%s%s", "converter", File.separator, "shorelines-fc.geojson")), "UTF-8");
	}

	/**
	 * Test conversion of GeoJSON with no geometry
	 */
	@Test
	public void testEmptyGeometryGeoPackageConversion() throws UserException {
		byte[] geoJsonBytes = emptyGeoJson.getBytes();
		geoPackageConverter.apply(geoJsonBytes);
	}

	/**
	 * Test conversion of GeoJSON with shorelines input
	 */
	@Test
	public void testGeoPackageConversion() throws UserException {
		byte[] geoJsonBytes = shorelinesGeoJson.getBytes();
		geoPackageConverter.apply(geoJsonBytes);
	}

	/**
	 * Test conversion of GeoJSON with no geometry
	 */
	@Test
	public void testEmptyGeometryShapefileConversion() throws UserException {
		byte[] geoJsonBytes = emptyGeoJson.getBytes();
		shapefileConverter.apply(geoJsonBytes);
	}

	/**
	 * Test conversion of GeoJSON with shoreline geometry
	 */
	@Test
	public void testShapefileConversion() throws UserException {
		byte[] geoJsonBytes = shorelinesGeoJson.getBytes();
		shapefileConverter.apply(geoJsonBytes);
	}
}
