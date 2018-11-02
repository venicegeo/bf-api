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

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.geotools.feature.DefaultFeatureCollection;
import org.geotools.feature.FeatureCollection;
import org.geotools.feature.FeatureIterator;
import org.geotools.feature.NameImpl;
import org.geotools.feature.simple.SimpleFeatureBuilder;
import org.geotools.feature.simple.SimpleFeatureTypeBuilder;
import org.geotools.feature.type.AttributeDescriptorImpl;
import org.geotools.feature.type.AttributeTypeImpl;
import org.geotools.feature.type.GeometryDescriptorImpl;
import org.geotools.feature.type.GeometryTypeImpl;
import org.geotools.referencing.crs.DefaultGeographicCRS;
import org.opengis.feature.Feature;
import org.opengis.feature.Property;
import org.opengis.feature.simple.SimpleFeature;
import org.opengis.feature.simple.SimpleFeatureType;
import org.opengis.feature.type.AttributeDescriptor;
import org.opengis.feature.type.AttributeType;
import org.opengis.feature.type.FeatureType;
import org.opengis.feature.type.GeometryDescriptor;
import org.opengis.feature.type.GeometryType;
import org.opengis.feature.type.Name;
import org.opengis.feature.type.PropertyDescriptor;
import org.opengis.feature.type.PropertyType;
import org.springframework.http.HttpStatus;
import org.venice.beachfront.bfapi.model.exception.UserException;

import com.vividsolutions.jts.geom.Geometry;

/**
 * Implementation of the {@link AbstractConverter} interface.
 *
 * @version 1.0
 */
public abstract class AbstractConverter {
	
	private static Map<String, String> PROPERTIES = createProperties();
	private static Map<String, String> createProperties(){
		HashMap<String, String> result = new HashMap<>();
		result.put("algorithm_name", "algo_name");
		result.put("algorithm_id", "algo_id");
		result.put("algorithm_version", "algo_vers");
		result.put("cloud_cover", "cld_cover");
		result.put("resolution", "res");
		result.put("classification", "class");
		result.put("time_of_collect", "time");
		result.put("tide_min_24h", "tide_min");
		result.put("tide_max_24h", "tide_max");
		result.put("sensor_name", "sensor");
		result.put("src_horizontal_accuracy", "horiz_acc");
		return result;
	}
	protected SimpleFeatureType createSimpleFeatureType(FeatureCollection<?, ?> fc) throws UserException{
        FeatureType inputFeatureType = fc.getSchema();

        if (inputFeatureType == null){
        	throw new UserException("The feature collection provided has no schema.", HttpStatus.INTERNAL_SERVER_ERROR);
        }
        
        // Feature Type
        SimpleFeatureTypeBuilder sftb = new SimpleFeatureTypeBuilder();
        sftb.setName(inputFeatureType.getName());
        sftb.setCRS(DefaultGeographicCRS.WGS84);
        List<AttributeDescriptor> ads = new ArrayList<>();
        GeometryDescriptor gd = inputFeatureType.getGeometryDescriptor();
        GeometryType gt = gd.getType();
        Name geometryName = new NameImpl("the_geom");
        gt = new GeometryTypeImpl(geometryName, gt.getBinding(), 
        		DefaultGeographicCRS.WGS84, 
        		gt.isIdentified(), 
        		gt.isAbstract(), gt.getRestrictions(), 
        		gt.getSuper(), 
        		gt.getDescription());
        gd = new GeometryDescriptorImpl(gt, 
        		geometryName, 
        		gd.getMinOccurs(), 
        		gd.getMaxOccurs(), 
        		gd.isNillable(), 
        		gd.getDefaultValue());
        ads.add(gd);
        for (PropertyDescriptor pd : inputFeatureType.getDescriptors()){
        	AttributeDescriptor ad = (AttributeDescriptor)pd;
        	String propertyName = pd.getName().getLocalPart();
        	if (propertyName == "geometry") {
        		continue;
        	}else {
    			if (PROPERTIES.containsKey(propertyName)) {
        			propertyName = PROPERTIES.get(propertyName);
    			}
            	PropertyType pt = pd.getType();
            	NameImpl pn = new NameImpl(propertyName);
            	AttributeType at = new AttributeTypeImpl(pn, 
            			pt.getBinding(), 
            			false, 
            			pt.isAbstract(), 
            			null, 
            			null, 
            			pt.getDescription());

            	ad = new AttributeDescriptorImpl(at, 
            			pn, 
            			pd.getMinOccurs(),
            			pd.getMaxOccurs(), 
            			pd.isNillable(), 
            			null);
        	}
        	ads.add(ad);
        }
        sftb.addAll(ads);
        SimpleFeatureType featureType = sftb.buildFeatureType();
        return featureType;
	}
	    
    protected DefaultFeatureCollection fcToSFC(FeatureCollection<?, ?> input, SimpleFeatureType featureType){
    	DefaultFeatureCollection result = new DefaultFeatureCollection();
    	SimpleFeatureBuilder sfb = new SimpleFeatureBuilder(featureType);
    	
    	FeatureIterator<?> fi = input.features();
    	Name destinationGPN = new NameImpl("the_geom");
    	while(fi.hasNext()){
    		Feature feature = fi.next();
    		sfb.reset();
    		
    		// Geometry
    		Name gpn = feature.getDefaultGeometryProperty().getName();
    		Geometry geometry = (Geometry)feature.getProperty(gpn).getValue();
    		geometry.setSRID(4326);
			sfb.set(destinationGPN, geometry);

			// Other properties
    		Collection<Property> properties = feature.getProperties();
    		for (Property property : properties) {
    			String propertyName = property.getName().getLocalPart();
    			if (propertyName == "geometry"){
    				continue;
    			}
    			Object value = property.getValue();
    			if (PROPERTIES.containsKey(propertyName)) {
        			sfb.set(PROPERTIES.get(propertyName), value);
    			} else {
        			sfb.set(propertyName, value);
    			}
    		}

    		SimpleFeature sf = sfb.buildFeature(feature.getIdentifier().getID());    	

    		result.add(sf);
    	}
    	return result;
    }
}
