package org.venice.beachfront.bfapi.model;

import org.junit.Assert;
import org.junit.Test;

import java.util.HashSet;

public class JobUserPKTest {

    @Test
    public void testPojo() {
        Job j1 = new Job();
        j1.setJobId("id_1");

        Job j2 = new Job();
        j2.setJobId("id_2");

        UserProfile user1 = new UserProfile();
        user1.setUserId("user_id_1");

        UserProfile user2 = new UserProfile();
        user2.setUserId("user_id_2");

        JobUserPK pk1 = new JobUserPK(j1, user1);
        JobUserPK pk2 = new JobUserPK(j2, user2);
        JobUserPK pk3 = new JobUserPK(pk1.getJob(), pk1.getUser());
        JobUserPK pk4 = new JobUserPK();
        pk4.setJob(pk2.getJob());
        pk4.setUser(pk2.getUser());

        HashSet<JobUserPK> set = new HashSet<>();

        Assert.assertTrue(set.add(pk1));
        Assert.assertTrue(set.add(pk2));
        Assert.assertFalse(set.add(pk3));
        Assert.assertFalse(set.add(pk4));

        Assert.assertFalse(pk1.equals(null));
        Assert.assertFalse(pk1.equals(new Object()));
        Assert.assertTrue(pk1.equals(pk1));
    }
}