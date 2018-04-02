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
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.Reader;
import java.io.Serializable;
import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;

import org.geotools.data.DataStore;
import org.geotools.data.DefaultTransaction;
import org.geotools.data.FileDataStoreFactorySpi;
import org.geotools.data.Transaction;
import org.geotools.data.shapefile.ShapefileDataStoreFactory;
import org.geotools.data.simple.SimpleFeatureSource;
import org.geotools.data.simple.SimpleFeatureStore;
import org.geotools.feature.FeatureCollection;
import org.geotools.geojson.feature.FeatureJSON;
import org.geotools.geojson.geom.GeometryJSON;
import org.opengis.feature.simple.SimpleFeatureType;
import org.springframework.stereotype.Service;
import org.venice.beachfront.bfapi.model.exception.UserException;

/**
 * Implementation of the {@link AbstractConverter} class for Shapefiles.
 *
 * @version 2.0
 */
@Service
public class ShapefileConverter extends AbstractConverter{
		
    /**
     * Perform the actual conversion from GeoJSON to Shapefile.
     *
     * @param geojson A byte array containing GeoJSON data
     * @return A byte array containing SHP data in a .zip
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

            // DataStore
            FileDataStoreFactorySpi factory = new ShapefileDataStoreFactory();
    		File shapefile = File.createTempFile("shorelines", ".shp");
            Map<String, Serializable> params = new HashMap<String, Serializable>();
            params.put("url", shapefile.toURI().toURL());
            params.put("create spatial index", Boolean.TRUE);            
            DataStore dataStore = factory.createNewDataStore(params);

            SimpleFeatureType featureType = createSimpleFeatureType(fc);
            dataStore.createSchema(featureType);

            // Feature Store
            String typeName = dataStore.getTypeNames()[0];
            SimpleFeatureSource featureSource = dataStore.getFeatureSource(typeName);
            SimpleFeatureStore featureStore = (SimpleFeatureStore) featureSource;

            // Transaction
            Transaction transaction = new DefaultTransaction("create");
            featureStore.setTransaction(transaction);
            try {
            	featureStore.addFeatures(fcToSFC(fc, featureType));
                transaction.commit();
            } catch (Exception problem) {
                problem.printStackTrace();
                transaction.rollback();
            } finally {
                transaction.close();
            }
            
            File zipFile = zipResults(shapefile);

            // Return the results
            result = java.nio.file.Files.readAllBytes(zipFile.toPath());
            
            cleanup(shapefile);
            cleanup(zipFile);
        } catch (Exception e) {
            throw new UserException("Failed to export to Shapefile: " + e.getMessage(), e, org.springframework.http.HttpStatus.INTERNAL_SERVER_ERROR);
        }
        return result;
    }

    private File zipResults(File input) throws IOException {
    	File result = File.createTempFile("shorelines", ".zip");

        byte[] buffer = new byte[1024];
        FileOutputStream fos = null;
        ZipOutputStream zos = null;
        try {
            fos = new FileOutputStream(result);
            zos = new ZipOutputStream(fos);

            FileInputStream in = null;
            
            for (File file: getFiles(input)) {
                System.out.println("File Added : " + file);
                ZipEntry ze = new ZipEntry(file.getName());
                zos.putNextEntry(ze);
                try {
                    in = new FileInputStream(file.getAbsolutePath());
                    int len;
                    while ((len = in .read(buffer)) > 0) {
                        zos.write(buffer, 0, len);
                    }
                } finally {
                    in.close();
                }
            }

            zos.closeEntry();
            System.out.println("Folder successfully compressed");

        } catch (IOException ex) {
            ex.printStackTrace();
        } finally {
            try {
                zos.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        
    	return result;
    }
    
    private File[] getFiles(File rootFile){
    	File[] result = new File[0];
    	ArrayList<File> files = new ArrayList<File>();
    	String fileName = rootFile.getName();
    	FilenameFilter ff = new FilenameFilter(fileName);
        File parentFile = rootFile.getParentFile();
        for (String filename: parentFile.list()) {
        	if (ff.accept(rootFile, filename)) {
        		files.add(new File(parentFile, filename));
        	}
        }
        
        return files.toArray(result);
    }
    
    /**
     * Remove the temporary files that were created
     * @param shapefile
     * @return the list of files that weren't deleted 
     * (possibly useful for error reporting)
     */
    private Set<File> cleanup(File shapefile){
    	
    	final Set<File> result = new HashSet<File>();
    	final File folder = new File(shapefile.getParent());
		final File[] files = folder.listFiles(new FilenameFilter(shapefile.getName()));
		for ( final File file : files ) {
		    if ( !file.delete() ) {
		        System.err.println( "Can't remove " + file.getAbsolutePath() );
		    	result.add(file);
		    }
		}    
		return result;
	}
    
    private class FilenameFilter implements java.io.FilenameFilter {
    	FilenameFilter(String fileName){
    		this.root = fileName.substring(0, fileName.lastIndexOf('.'));
    	}
    	private String root;

		@Override
		public boolean accept(File dir, String name) {
			return name.startsWith(root);
		}
    }
}
