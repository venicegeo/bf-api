package org.venice.beachfront.bfapi.services.converter;

/**
 * Special exception class for handling an error during the conversion process.
 */
public class ConversionError extends RuntimeException {
    /**
     * Create a new GeoPackageConversionError.
     * 
     * @param cause A {@link Throwable} that is the real cause of the failure
     */
    public ConversionError(Throwable cause) {
        super(cause);
    }
}